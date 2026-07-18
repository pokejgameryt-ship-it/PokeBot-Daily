{ pkgs }: {
  deps = [
    pkgs.python311
    pkgs.python311Packages.pip
    pkgs.tesseract
    pkgs.tesseract-data-eng
    pkgs.tesseract-data-spa
  ];
}
