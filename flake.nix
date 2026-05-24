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
        in
        {
          default = pkgs.mkShell {
            packages = with pkgs; [
              # nodejs_20 is often marked insecure on nixpkgs-unstable; 22 satisfies package.json (>=18)
              nodejs_22
              python3
              pandoc
              librsvg
              # XeLaTeX + latexmk for multi-pass PDF (citations, longtable)
              texlive.combined.scheme-medium
              texlive.packages.latexmk
            ];

            shellHook = ''
              if [ ! -d .venv ]; then
                python3 -m venv .venv
              fi
              source .venv/bin/activate
              pip install -q -r requirements.txt 2>/dev/null \
                || pip install -r requirements.txt
              echo "MWI lecture shell: make site | make figures | make script-pdf"
            '';
          };
        });
    };
}
