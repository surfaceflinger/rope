{
  buildPythonPackage,
  fetchPypi,
  setuptools,
  sympy,
  tqdm,
  lightecc,
}:

buildPythonPackage rec {
  pname = "lightphe";
  version = "0.0.22";
  pyproject = true;

  src = fetchPypi {
    inherit pname version;
    hash = "sha256-4H5gDC4q/f/v5b/pVOXEclPcuM04Nvgu0kFaLwp0/vM=";
  };

  postPatch = ''
    touch README.md requirements.txt
    sed -i '/data_files/d' setup.py || true
  '';

  build-system = [ setuptools ];
  dependencies = [
    sympy
    tqdm
    lightecc
  ];
  doCheck = false;
}
