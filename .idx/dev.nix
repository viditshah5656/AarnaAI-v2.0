# Firebase IDX / Studio SAFE configuration

{ pkgs, ... }: {

  channel = "stable-24.05";

  packages = [
    pkgs.sudo
    pkgs.python310
    pkgs.git
    pkgs.curl
  ];

  env = {
    PYTHONUNBUFFERED = "1";
    PIP_DISABLE_PIP_VERSION_CHECK = "1";
  };

  idx = {
    extensions = [
      "ms-python.python"
      "ms-toolsai.jupyter"
    ];

    workspace = {
      onCreate = {
        setup-python = ''
          python -m ensurepip --upgrade
          python -m pip install --upgrade pip
        '';
      };
    };
  };
}
