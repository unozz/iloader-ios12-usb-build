# iLoader iOS 12 USB build

Minimal local-use correction to upstream [iLoader 2.4.0](https://github.com/nab138/iloader/tree/v2.4.0).
This project is not affiliated with upstream iLoader and does not contain Guitar Unos.

The source revision is pinned to `902597564315442f00ab299dcc758ee0e13b8fa8`.
The patch skips the wireless-debugging setting request only for iOS 12 USB
connections. Obtaining the existing pairing record and starting a trusted
lockdown session still have to succeed. Other OS versions/network connections
retain upstream behavior. Authentication and IPA signing code are unchanged.

## Build and limits

The workflow uses GitHub's standard `macos-15` Apple Silicon runner and refuses
private repositories. It builds a separate Mac application with one Cargo job,
without a Developer ID certificate, updater signing key or account secrets.
Artifacts are retained for one day. No Apple Account credentials, device trust
records, Guitar Unos source, projects, recordings or samples belong in this repo.

The resulting Mac app is ad-hoc signed for local testing, not notarized or
Developer ID signed. macOS may require the owner to approve opening it through
normal system controls. Never disable Gatekeeper or system security protections.
It is not automatically installed or launched, and does not itself install an IPA.
The upstream bundle identifier is retained; do not run it alongside another
iLoader instance. It may use the same upstream preferences/keychain service.

Completed checks so far: source patch applies/reverses cleanly, exact source
module hashes are checked, and the Python build helper parses successfully.
The source correction is NOT yet compiled or tested on a device. Build success
would not prove device selection, signing or installation work on iOS 12.

Publish only these five reviewed files: this README, LICENSE,
`iloader-v2.4.0-legacy-usb.patch`, `build_iloader.py`,
`.github/workflows/build.yml`.

GitHub reference: https://docs.github.com/en/actions/reference/runners/github-hosted-runners
