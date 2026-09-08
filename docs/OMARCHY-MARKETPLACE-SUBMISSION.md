# Omarchy Plugin Marketplace Submission Guide

This document outlines the procedure to propose `omarchy-screensaver-studio` (`daemon0.screensaver-studio`) for inclusion in the official Omarchy Plugin Marketplace.

## Prerequisites

1. **Public Repository**: Ensure this repository is published publicly on GitHub under your account:
   `https://github.com/YOUR-USERNAME/omarchy-screensaver-studio.git`
2. **Strict Manifest Validation**:
   Validate the plugin manifest locally against Omarchy's schema:
   ```bash
   omarchy plugin validate .
   ```
   The command must return exit code `0` with no warnings.
3. **End-to-End Installation Testing**:
   Verify complete lifecycle execution:
   ```bash
   # 1. Test installation directly from Git
   omarchy plugin add https://github.com/YOUR-USERNAME/omarchy-screensaver-studio.git --enable --yes

   # 2. Verify status and discovery
   omarchy plugin list | grep "daemon0.screensaver-studio"

   # 3. Test runtime disable and enable
   omarchy plugin disable daemon0.screensaver-studio
   omarchy plugin enable daemon0.screensaver-studio

   # 4. Test plugin update
   omarchy plugin update daemon0.screensaver-studio --yes

   # 5. Test clean removal
   omarchy plugin remove daemon0.screensaver-studio --yes
   ```

## Submission Steps

1. Review the official Omarchy marketplace publishing documentation:
   `https://omarchy.org/docs/marketplace/`
2. Prepare your submission details:
   - **Repository URL**: `https://github.com/YOUR-USERNAME/omarchy-screensaver-studio.git`
   - **Plugin Identifier**: `daemon0.screensaver-studio`
   - **Category**: System / Productivity / Desktop
   - **Tags**: omarchy, quickshell, wayland, hyprland
   - **License**: MIT
   - **Primary Maintainer**: Your GitHub handle
3. Submit the plugin submission form on the official Omarchy site or open a pull request against the official Omarchy plugin catalog repository.
4. **Important Notice**: Marketplace approval is evaluated by official maintainers and is not guaranteed or automatic. Do not state or imply that the plugin is officially listed until your submission has been formally reviewed and merged.
