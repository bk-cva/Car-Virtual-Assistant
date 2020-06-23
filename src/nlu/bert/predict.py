import os.path
import pickle
from absl import logging
import tensorflow as tf

from .modeling import BertConfig, BertModel, get_assignment_map_from_checkpoint
from .tokenization import convert_to_unicode, FullTokenizer


class InputExample(object):
    """A single training/test example for simple sequence classification."""

    def __init__(self, guid, text, label=None):
        """Constructs a InputExample.

        Args:
          guid: Unique id for the example.
          text: string. The untokenized text of the first sequence. For single
            sequence tasks, only this sequence must be specified.
          label: (Optional) string. The label of the example. This should be
            specified for train and dev examples, but not for test examples.
        """
        self.guid = guid
        self.text = text
        self.label = label


class InputFeatures(object):
    """A single set of features of data."""

    def __init__(self,
                 input_ids,
                 mask):
        self.input_ids = input_ids
        self.mask = mask


class NerProcessor:
    def get_test_examples(self, item: str):
        fake_labels = ' '.join(['O' for _ in item.split(' ')])
        return self._create_example(
            [(fake_labels, item)], "test"
        )

    def _create_example(self, lines, set_type):
        examples = []
        for (i, line) in enumerate(lines):
            guid = "%s-%s" % (set_type, i)
            texts = convert_to_unicode(line[1])
            labels = convert_to_unicode(line[0])
            examples.append(InputExample(guid=guid, text=texts, label=labels))
        return examples


def convert_single_example(example, max_seq_length, tokenizer):
    """
    :param example:
    :param max_seq_length:
    :param tokenizer: WordPiece tokenization
    :return: feature

    IN this part we should rebuild input sentences to the following format.
    example:[Jim,Hen,##son,was,a,puppet,##eer]

    """
    textlist = example.text.split(' ')
    tokens = []
    for word in textlist:
        token = tokenizer.tokenize(word)
        tokens.extend(token)
    # only Account for [CLS] with "- 1".
    if len(tokens) >= max_seq_length - 1:
        tokens = tokens[0:(max_seq_length - 1)]
    ntokens = ["[CLS]"]
    for token in tokens:
        ntokens.append(token)
    # after that we don't add "[SEP]" because we want a sentence don't have
    # stop tag, because i think its not very necessary.
    # or if add "[SEP]" the model even will cause problem, special the crf layer was used.
    input_ids = tokenizer.convert_tokens_to_ids(ntokens)
    mask = [1]*len(input_ids)
    # use zero to padding and you should
    while len(input_ids) < max_seq_length:
        input_ids.append(0)
        mask.append(0)
        ntokens.append("[PAD]")

    feature = InputFeatures(
        input_ids=input_ids,
        mask=mask,
    )
    # we need ntokens because if we do predict it can help us return to original token.
    return feature, ntokens


def crf_loss(logits, labels, num_labels, mask2len):
    """
    :param logits:
    :param labels:
    :param mask2len:each sample's length
    :return:
    """
    with tf.variable_scope("crf_loss"):
        trans = tf.get_variable(
            "transition",
            shape=[num_labels, num_labels],
            initializer=tf.contrib.layers.xavier_initializer()
        )

    _, transition = tf.contrib.crf.crf_log_likelihood(
        logits, labels, transition_params=trans, sequence_lengths=mask2len)

    return transition


def create_model(bert_config, is_training, input_ids, mask,
                 segment_ids, labels, num_intent_labels, num_entity_labels):
    model = BertModel(
        config=bert_config,
        is_training=is_training,
        input_ids=input_ids,
        input_mask=mask,
        token_type_ids=segment_ids,
        use_one_hot_embeddings=False
    )

    # The 12th encoder output is used to feed to the CRF layer to output the entity name
    # While the last encoder (16th) is used to feed to the mean and fc layers to output the intent.
    ner_output_layer, *_, intent_output_layer = model.get_all_encoder_layers()[-5:]

    logits = tf.keras.layers.Dense(
        num_entity_labels, activation=None, name='ner/logits')(ner_output_layer)
    mask2len = tf.reduce_sum(mask, axis=1)
    trans = crf_loss(logits, labels, num_entity_labels, mask2len)
    ner_predict, _ = tf.contrib.crf.crf_decode(logits, trans, mask2len)

    mean_layer = tf.reduce_sum(intent_output_layer, axis=1) / \
        tf.cast(tf.reshape(tf.reduce_sum(mask, axis=1), (-1, 1)), tf.float32)
    hidden_layer = tf.keras.layers.Dense(
        256, activation='relu', name='intent/hiddens')(mean_layer)
    logits = tf.keras.layers.Dense(
        num_intent_labels, activation=None, name='intent/outputs')(hidden_layer)
    intent_predict = tf.math.argmax(logits, axis=-1)
    return ner_predict, intent_predict


class BertPredictor:
    def __init__(self, model_dir):
        self.bert_config_file = os.path.join(model_dir, 'bert_config.json')
        self.init_checkpoint = tf.train.latest_checkpoint(model_dir)
        self.vocab_file = os.path.join(model_dir, 'vocab.txt')
        self.max_seq_length = 64
        self.do_lower_case = False

        bert_config = BertConfig.from_json_file(self.bert_config_file)

        if self.max_seq_length > bert_config.max_position_embeddings:
            raise ValueError(
                "Cannot use sequence length %d because the BERT model "
                "was only trained up to sequence length %d" %
                (self.max_seq_length, bert_config.max_position_embeddings))

        self.processor = NerProcessor()

        self.tokenizer = FullTokenizer(
            vocab_file=self.vocab_file, do_lower_case=self.do_lower_case)

        with open(os.path.join(model_dir, 'entities_label2id.pkl'), 'rb') as rf:
            label2id_dict = pickle.load(rf)
            self.entities_id2label = {
                value: key for key, value in label2id_dict.items()}

        with open(os.path.join(model_dir, 'intents_label2id.pkl'), 'rb') as rf:
            label2id_dict = pickle.load(rf)
            self.intents_id2label = {
                value: key for key, value in label2id_dict.items()}

        self.input_ids = tf.placeholder(tf.int32, shape=[1, self.max_seq_length])
        self.mask = tf.placeholder(tf.int32, shape=[1, self.max_seq_length])
        segment_ids = tf.zeros(shape=[1, self.max_seq_length], dtype=tf.int32)
        label_ids = tf.zeros(shape=[1, self.max_seq_length], dtype=tf.int32)
        self.ner_predicts, self.intent_predicts = create_model(bert_config, False, self.input_ids,
                                                               self.mask, segment_ids, label_ids,
                                                               len(self.intents_id2label), len(self.entities_id2label))
        tvars = tf.trainable_variables()
        (assignment_map, initialized_variable_names) = get_assignment_map_from_checkpoint(
            tvars, self.init_checkpoint)
        tf.train.init_from_checkpoint(self.init_checkpoint, assignment_map)
        logging.info("**** Trainable Variables ****")
        for var in tvars:
            init_string = ""
            if var.name in initialized_variable_names:
                init_string = ", *INIT_FROM_CKPT*"
            logging.info("  name = %s, shape = %s%s", var.name, var.shape,
                         init_string)

        self.sess = tf.Session()
        self.sess.run(tf.global_variables_initializer())

    def predict(self, item: str):
        predict_example = self.processor.get_test_examples(item)[0]
        feature, ntokens = convert_single_example(
            predict_example, self.max_seq_length, self.tokenizer)

        ner_predictions, intent_predictions = self.sess.run([self.ner_predicts, self.intent_predicts], {
            self.input_ids: [feature.input_ids],
            self.mask: [feature.mask],
        })

        ner_results = []
        for i, prediction in enumerate(ner_predictions[0]):
            token = ntokens[i]
            predict = self.entities_id2label[prediction]
            if token != "[PAD]" and token != "[CLS]":
                if token.startswith("##"):
                    ner_results[-1][1] += token[2:]
                    continue
                if predict == 'X':
                    ner_results[-1][1] += token
                    continue
                ner_results.append([predict, token])

        return self.intents_id2label[intent_predictions[0]], ner_results
