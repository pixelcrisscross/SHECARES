
{ pkgs, ... }: {
  # For more information on configuring your environment, see
  # https://www.firebase.google.com/docs/studio/customize-workspace
  channel = "stable-24.05"; # The Nixpkgs channel to use.
  packages = [
    pkgs.nodejs_22 # Use Node.js version 22
  ];
  env = {
    # Set the Gemini API key as an environment variable
    GEMINI_API_KEY = "AIzaSyCfBmfEsoo03l3j7xuoVEP8pEbVhsUPyTE";
  };
  idx = {
    extensions = [
      "dbaeumer.vscode-eslint" # Add ESLint for code linting
    ];
    workspace = {
      # Commands to run when the workspace is first created
      onCreate = {
        npm-install = "npm install";
      };
      # Commands to run when the workspace is started or restarted
      onStart = {
        dev-server = "npm run dev";
      };
    };
    previews = {
      enable = true;
      previews = {
        web = {
          command = ["npm" "run" "dev" "--" "--port" "$PORT"];
          manager = "web";
        };
      };
    };
  };
}
