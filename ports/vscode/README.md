# datum for VS Code

A light and dark color theme derived from color science. Part of
[datum](https://github.com/w0zro/datum) — see [datum.w0zro.com](https://datum.w0zro.com).

Pick **datum (dark)** or **datum (light)** in *Preferences → Color Theme*.

## Install

This folder is a self-contained VS Code extension (the theme JSON in `themes/` is
generated from the datum palette — don't edit it by hand).

**From the Marketplace / Open VSX** (once published): search "datum".

**Local, without publishing:**

```sh
# option A — package and install a .vsix
npm i -g @vscode/vsce
cd ports/vscode && vsce package
code --install-extension datum-0.1.0.vsix

# option B — symlink the folder into your extensions dir
ln -s "$PWD" ~/.vscode/extensions/datum
```

Then reload VS Code and choose the theme.
