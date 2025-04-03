# Bill Tracker OCR Installation

To enable the OCR functionality for receipt scanning, you need to install the following packages:

```
pip install opencv-python pytesseract pillow
```

Additionally, you need to install Tesseract OCR on your system:

## Windows
1. Download and install Tesseract from: https://github.com/UB-Mannheim/tesseract/wiki
2. Make sure to add Tesseract to your PATH

## macOS
```
brew install tesseract
```

## Linux (Ubuntu/Debian)
```
sudo apt-get install tesseract-ocr
```

After installation, the 'Scan Receipt' button will be enabled in the application. 