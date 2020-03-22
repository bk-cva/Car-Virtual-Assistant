# Car Virtual Assistant

Virtual Assistant for Car using Natual Language Processing.

## Prerequisites
- Docker

## Get Started
Download BERT NER & Intent models and place them at `src/nlp/entities/models` & `src/nlp/intents/models`.

Build docker image:
```bash
docker build -t cva .
```
Run:
```bash
docker run -it --rm -p 5000:5000 cva
```

Test it by sending a HTTP POST request to `http://localhost:5000/analyze` with a JSON body as following:
```json
{
	"texts": [
		"đến địa chỉ 268, đường Lý Thường Kiệt, phường 14, quận 10",
		"cho tôi đến ký túc xá Bách Khoa",
		"gọi điện cho thầy Thơ"
	]
}
```