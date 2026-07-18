{ pkgs }: {
  deps = [
    pkgs.python311
    pkgs.python311Packages.pip
  ];
  shell = ''
    apt-get update && apt-get install -y tesseract-ocr tesseract-ocr-eng tesseract-ocr-spa
  '';
}
