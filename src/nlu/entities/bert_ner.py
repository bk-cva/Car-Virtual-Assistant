import os.path
import pickle
from absl import logging
import tensorflow as tf

from ..common import MODEL_DIR
from .bert_modeling import BertConfig, BertModel, get_assignment_map_from_checkpoint
from .bert_tokenization import convert_to_unicode, FullTokenizer

bert_config_file = os.path.join(MODEL_DIR, 'bert_config.json')
init_checkpoint = tf.train.latest_checkpoint(MODEL_DIR)
label2id = os.path.join(MODEL_DIR, 'label2id.pkl')
vocab_file = os.path.join(MODEL_DIR, 'vocab.txt')
output_dir = 'output'
max_seq_length = 64
do_lower_case = False
predict_batch_size = 1


class InputExample(object):
    """A single training/test example for simple sequence classification."""

    def __init__(self, guid, text, label=None):
        """Constructs a InputExample.

        Args:
          guid: Unique id for the example.
          text_a: string. The untokenized text of the first sequence. For single
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

    def get_labels(self):
        """
        here "X" used to represent "##eer","##soo" and so on!
        "[PAD]" for padding
        :return:
        """
        return ['[PAD]', 'O', 'X', '[CLS]', '[SEP]', 'B-place', 'I-place', 'B-place_property', 'I-place_property',
                'B-route_property', 'I-route_property', 'B-district', 'I-district', 'B-ward', 'I-ward',
                'B-place_name', 'I-place_name', 'B-info_type', 'I-info_type', 'B-personal_place',
                'B-street', 'I-street', 'I-personal_place', 'B-address', 'B-schedule_type', 'I-schedule_type',
                'B-time', 'I-time', 'B-date', 'I-date', 'B-action_type', 'B-side', 'B-quantity',
                'B-remind_content', 'I-remind_content', 'B-period', 'I-period', 'B-music_genre', 'I-music_genre',
                'B-musician', 'I-musician', 'B-song_name', 'I-song_name', 'I-action_type', 'B-location',
                'B-schedule_property', 'I-schedule_property', 'B-air_type', 'I-air_type', 'B-air_temp', 'I-air_temp',
                'B-news_topic', 'I-news_topic', 'I-location', 'B-radio_channel', 'I-radio_channel']

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
    ntokens = []
    ntokens.append("[CLS]")
    for token in tokens:
        ntokens.append(token)
    # after that we don't add "[SEP]" because we want a sentence don't have
    # stop tag, because i think its not very necessary.
    # or if add "[SEP]" the model even will cause problem, special the crf layer was used.
    input_ids = tokenizer.convert_tokens_to_ids(ntokens)
    mask = [1]*len(input_ids)
    #use zero to padding and you should
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


def hidden2tag(hiddenlayer, numclass):
    linear = tf.keras.layers.Dense(numclass, activation=None)
    return linear(hiddenlayer)


def crf_loss(logits, labels, mask, num_labels, mask2len):
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

    log_likelihood, transition = tf.contrib.crf.crf_log_likelihood(
        logits, labels, transition_params=trans, sequence_lengths=mask2len)
    loss = tf.math.reduce_mean(-log_likelihood)

    return loss, transition


def softmax_layer(logits, labels, num_labels, mask):
    logits = tf.reshape(logits, [-1, num_labels])
    labels = tf.reshape(labels, [-1])
    mask = tf.cast(mask, dtype=tf.float32)
    one_hot_labels = tf.one_hot(labels, depth=num_labels, dtype=tf.float32)
    loss = tf.losses.softmax_cross_entropy(
        logits=logits, onehot_labels=one_hot_labels)
    loss *= tf.reshape(mask, [-1])
    loss = tf.reduce_sum(loss)
    total_size = tf.reduce_sum(mask)
    total_size += 1e-12  # to avoid division by 0 for all-0 weights
    loss /= total_size
    # predict not mask we could filtered it in the prediction part.
    probabilities = tf.math.softmax(logits, axis=-1)
    predict = tf.math.argmax(probabilities, axis=-1)
    return loss, predict


def create_model(bert_config, is_training, input_ids, mask,
                 segment_ids, labels, num_labels, use_one_hot_embeddings):
    model = BertModel(
        config=bert_config,
        is_training=is_training,
        input_ids=input_ids,
        input_mask=mask,
        token_type_ids=segment_ids,
        use_one_hot_embeddings=use_one_hot_embeddings
    )

    output_layer = model.get_sequence_output()
    logits = hidden2tag(output_layer, num_labels)
    logits = tf.reshape(logits, [-1, max_seq_length, num_labels])
    mask2len = tf.reduce_sum(mask, axis=1)
    loss, trans = crf_loss(logits, labels, mask, num_labels, mask2len)
    predict, viterbi_score = tf.contrib.crf.crf_decode(
        logits, trans, mask2len)
    return (loss, logits, predict)


logging.set_verbosity(logging.INFO)
processors = {"ner": NerProcessor}
bert_config = BertConfig.from_json_file(bert_config_file)
if max_seq_length > bert_config.max_position_embeddings:
    raise ValueError(
        "Cannot use sequence length %d because the BERT model "
        "was only trained up to sequence length %d" %
        (max_seq_length, bert_config.max_position_embeddings))
processor = processors['ner']()

label_list = processor.get_labels()

tokenizer = FullTokenizer(
    vocab_file=vocab_file, do_lower_case=False)

input_ids = tf.placeholder(tf.int32, shape=[1, 64])
mask = tf.placeholder(tf.int32, shape=[1, 64])
segment_ids = tf.zeros(shape=[1, 64], dtype=tf.int32)
label_ids = tf.zeros(shape=[1, 64], dtype=tf.int32)
(total_loss, logits, predicts) = create_model(bert_config, False, input_ids,
                                              mask, segment_ids, label_ids, len(label_list),
                                              use_one_hot_embeddings=False)
tvars = tf.trainable_variables()
(assignment_map, initialized_variable_names) = get_assignment_map_from_checkpoint(
    tvars, init_checkpoint)
tf.train.init_from_checkpoint(init_checkpoint, assignment_map)
logging.info("**** Trainable Variables ****")
for var in tvars:
    init_string = ""
    if var.name in initialized_variable_names:
        init_string = ", *INIT_FROM_CKPT*"
    logging.info("  name = %s, shape = %s%s", var.name, var.shape,
                init_string)

sess = tf.Session()
sess.run(tf.global_variables_initializer())

with open(label2id, 'rb') as rf:
    label2id = pickle.load(rf)
    id2label = {value: key for key, value in label2id.items()}


def predict(item: str):
    predict_examples = processor.get_test_examples(item)

    batch_tokens = []
    batch_features = {
        "input_ids": [],
        "mask": [],
    }
    for example in predict_examples:
        feature, ntokens = convert_single_example(example, max_seq_length, tokenizer)
        batch_tokens.extend(ntokens)
        batch_features["input_ids"].append(feature.input_ids)
        batch_features["mask"].append(feature.mask)

    predictions = sess.run(predicts, {
        input_ids: batch_features['input_ids'],
        mask: batch_features['mask'],
    })[0]

    result = []
    for i, prediction in enumerate(predictions):
        token = batch_tokens[i]
        predict = id2label[prediction]
        if token != "[PAD]" and token != "[CLS]":
            if token.startswith("##"):
                result[-1][0] += token[2:]
                continue
            if predict == 'X':
                result[-1][0] += token
                continue
            result.append([token, predict])

    return result
