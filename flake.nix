{
  description = "Build environment for MWI lecture (slides, figures, script PDF)";

  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";

  outputs = { self, nixpkgs }:
    let
      systems = [
        "x86_64-linux"
        "aarch64-linux"
        "x86_64-darwin"
        "aarch64-darwin"
      ];
      forEachSystem = nixpkgs.lib.genAttrs systems;
    in
    {
      devShells = forEachSystem (system:
        let
          pkgs = nixpkgs.legacyPackages.${system};
          # Pre-built wheels from nixpkgs — avoids pip/venv + libstdc++ issues in CI.
          pythonEnv = pkgs.python312.withPackages (ps: with ps; [
            matplotlib
            numpy
            pandas
            requests
            openpyxl
            pillow
          ]);
        in
        {
          default = pkgs.mkShell {
            packages = with pkgs; [
              nodejs_22
              pythonEnv
              pandoc
              librsvg
              texlive.combined.scheme-medium
            ];

            shellHook = ''
              export PATH="${pythonEnv}/bin:$PATH"
              echo "MWI lecture shell (Python from nixpkgs): make site | make figures | make script-pdf"
            '';
          };
        });
    };
}
