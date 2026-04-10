{
  buildPythonPackage,
  fetchPypi,
  setuptools,
  tqdm,
}:

buildPythonPackage rec {
  pname = "lightecc";
  version = "0.0.5";
  pyproject = true;

  src = fetchPypi {
    inherit pname version;
    hash = "sha256-XJOIr+Yp6KX+WhHCY+5/zbInQUCcqYMo7j6FCrSZgnw=";
  };

  postPatch = ''
    touch README.md requirements.txt
    sed -i '/data_files/d' setup.py || true
  '';

  build-system = [ setuptools ];
  dependencies = [ tqdm ];
  doCheck = false;
}
