{
  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";

  outputs =
    { nixpkgs, self, ... }:
    let
      system = "x86_64-linux";
      pkgs = nixpkgs.legacyPackages.${system};
      python = pkgs.python313;
      py = python.pkgs;

      lightecc = py.callPackage ./nix/lightecc.nix { };
      lightphe = py.callPackage ./nix/lightphe.nix { inherit lightecc; };
      deepface = pkgs.callPackage ./nix/deepface.nix {
        inherit (pkgs) fetchFromGitHub;
        inherit (py)
          buildPythonPackage
          fire
          flask
          flask-cors
          gdown
          gunicorn
          mtcnn
          numpy
          opencv4
          pandas
          pillow
          requests
          retinaface
          setuptools
          tensorflow
          tqdm
          ;
        inherit lightphe;
        inherit (pkgs) lib;
      };

      rope = py.buildPythonApplication {
        pname = "rope";
        version = "0.1.0";
        pyproject = true;
        src = self;
        build-system = [ py.setuptools ];
        dependencies = [
          deepface
          py.pillow
        ];
        doCheck = false;
      };
    in
    {
      packages.${system} = {
        default = rope;
        inherit
          rope
          deepface
          lightecc
          lightphe
          ;
      };

      devShells.${system}.default = pkgs.mkShell { packages = [ rope ]; };
    };
}
