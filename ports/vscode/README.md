![datum](https://raw.githubusercontent.com/w0zro/datum/main/docs/banner-panel.png)

# datum for VS Code

A light and dark color theme derived from color science. Part of
[datum](https://github.com/w0zro/datum) — see [datum.w0zro.com](https://datum.w0zro.com).

![datum dark](https://raw.githubusercontent.com/w0zro/datum/main/docs/preview-dark.png)
![datum light](https://raw.githubusercontent.com/w0zro/datum/main/docs/preview-light.png)

Pick **datum (dark)** or **datum (light)** in *Preferences → Color Theme*.

## Install

Search **datum** in the Extensions view, or:

```sh
code --install-extension w0zro.datum
```

It's on the [VS Marketplace](https://marketplace.visualstudio.com/items?itemName=w0zro.datum)
and [Open VSX](https://open-vsx.org/extension/w0zro/datum).

## Notes

The theme JSON in `themes/` is generated from the datum palette — don't edit it by
hand. To build the extension locally instead of installing from a registry:

```sh
cd ports/vscode && npm i -g @vscode/vsce && vsce package
code --install-extension datum-*.vsix
```
