# Base Sepolia validation — 2026-09-01

Evidence level: E2 observable replay. These transactions were founder-operated through the CLI. They prove public contract behavior, not independent use, PMF, or a judge-completable public product.

## Current validated release (v2)

- Source commit: `37d52f201fad4419d9332028805d29f2bf93f2e5`
- PoolRound: [`0xC998f3a0439b7365D3839A415168fF7A4FFAcd62`](https://sepolia.basescan.org/address/0xC998f3a0439b7365D3839A415168fF7A4FFAcd62)
- Deployment: [`0xbe4381dd2e80a15a2befeb2141980ccc741c288c94eaa8332daa29a1de9e7948`](https://sepolia.basescan.org/tx/0xbe4381dd2e80a15a2befeb2141980ccc741c288c94eaa8332daa29a1de9e7948)

The v2 source rejects duplicate active obligation digests, rejects late approval or contribution, lets either member reject a proposal before unanimous approval, clears active reservations on cancellation/expiry/settlement, and retains the v1 settlement/refund guarantees.

### V2 round 1 — exact settlement

- Obligation digest: `0x41a25f6023b1da1bfb26f2f27d9fefc80f517eb79b50de1a8b38f24ad548d8de`
- Create: [`0xd86d12a01d3d79dc8045135b8e5fe9ba320ac222eeac6b30116f80dd7590d1ba`](https://sepolia.basescan.org/tx/0xd86d12a01d3d79dc8045135b8e5fe9ba320ac222eeac6b30116f80dd7590d1ba)
- Member A approval: [`0xb68521247882509fa7c5acdbc710b88692b688cb797f66b799cf91015a63b899`](https://sepolia.basescan.org/tx/0xb68521247882509fa7c5acdbc710b88692b688cb797f66b799cf91015a63b899)
- Member B approval: [`0xc84887410a92df8df3ddc8bdf53776bc7ebf6263e6e5540c2f593681782b19f5`](https://sepolia.basescan.org/tx/0xc84887410a92df8df3ddc8bdf53776bc7ebf6263e6e5540c2f593681782b19f5)
- Member A contribution: [`0x8937bb87bf300b61e9d89a9899a0c8535e0acfb03457a0383f1fb7a54c42f94c`](https://sepolia.basescan.org/tx/0x8937bb87bf300b61e9d89a9899a0c8535e0acfb03457a0383f1fb7a54c42f94c)
- Member B contribution: [`0x04c278c3e2e6644266593af72fa601d7a18f06141ab42935bd272ee324e0afa0`](https://sepolia.basescan.org/tx/0x04c278c3e2e6644266593af72fa601d7a18f06141ab42935bd272ee324e0afa0)
- Settlement: [`0x1b30bf0fceac02cedf45422251bb1f8c1ac5f6267a2662e47ac586a70426da00`](https://sepolia.basescan.org/tx/0x1b30bf0fceac02cedf45422251bb1f8c1ac5f6267a2662e47ac586a70426da00)

Verified state: round status `Settled` (`4`), digest consumed, active reservation cleared, exact raw USDC contributions `250000/750000`.

### V2 round 2 — cancellation and independent claims

- Obligation digest: `0x1499db69f1d9eb2dae687f7e9cf9bdc46f075549dd6b6175c4b8aa0950f743c5`
- Create: [`0x00dd10fed31b378e696b34f976f1fc2152c668eaa96099538a34d5b6a7b74552`](https://sepolia.basescan.org/tx/0x00dd10fed31b378e696b34f976f1fc2152c668eaa96099538a34d5b6a7b74552)
- Member A cancellation request: [`0x2117eb13c3b472ce32d74259b6bfbb8c82f4adab99023d8723303da114df72fc`](https://sepolia.basescan.org/tx/0x2117eb13c3b472ce32d74259b6bfbb8c82f4adab99023d8723303da114df72fc)
- Member B cancellation request: [`0xec11b23dce54bc4ec62cd39e46a6a54bc2247900aa667296205df2a928e8c16a`](https://sepolia.basescan.org/tx/0xec11b23dce54bc4ec62cd39e46a6a54bc2247900aa667296205df2a928e8c16a)
- Member A refund: [`0x7602fdcab68404ea6ecadde5887f24df85dbeaf8ff16d84234f116030b0cb483`](https://sepolia.basescan.org/tx/0x7602fdcab68404ea6ecadde5887f24df85dbeaf8ff16d84234f116030b0cb483)
- Member B refund: [`0xbf8c21e3516499d47ca90f0f9b31e4372f8215acd74fe4c2cc369b2a84d7e8ff`](https://sepolia.basescan.org/tx/0xbf8c21e3516499d47ca90f0f9b31e4372f8215acd74fe4c2cc369b2a84d7e8ff)

Verified state: round status `Cancelled` (`5`), both contribution claims zero, active reservation cleared, PoolRound USDC balance zero. Deployment, settlement, final cancellation, and both refund receipts report success.

## Superseded v1 spike

The first deployment below proved the same public happy/refund branches, but was superseded after review found that duplicate pending digests and late contributions should fail earlier. It is retained as an honest audit trail and is not the current release.

## Deployment

- Network: Base Sepolia (`84532`)
- Commit containing the deployed contract source: `3bd2d9066f011f0301f42e8daee082005e626360`
- Canonical test USDC: `0x036CbD53842c5426634e7929541eC2318f3dCF7e`
- PoolRound: [`0x7825F79016E5b1b04466956c3A9b817D2a0bE6AC`](https://sepolia.basescan.org/address/0x7825F79016E5b1b04466956c3A9b817D2a0bE6AC)
- Deployment: [`0x895dcd8d2a09eed36a95caffd50833a0ba07e5e1f93c935d6da5c9eab8f435d0`](https://sepolia.basescan.org/tx/0x895dcd8d2a09eed36a95caffd50833a0ba07e5e1f93c935d6da5c9eab8f435d0)
- Member A: `0x7d287D5f5C40073aEF8bB92A485fC82e446EE7b9`
- Member B: `0xaB06eCBd04c5aF0540Efd730F27935Fc6fC9ADB7`
- Merchant: `0xbB568962CF24d4CeBBf5d48308aCdAE873B93202`

No private key is stored in the repository. The second member's test key is in macOS Keychain under service `pooldeal-base-sepolia`, account `member-b`.

## Round 1 — exact settlement

- Obligation digest: `0x1a1c2bfa18f0472b73dbd4a7eaff30c21da92d6a931707cf26891fa4120617b4`
- Member A amount: `250000` raw USDC (0.25)
- Member B amount: `750000` raw USDC (0.75)
- Create: [`0x84fa34de0a01a91a6da55bba71de60d0dcfbf6b1a1d41d4dd5ffb0d4403e1fbe`](https://sepolia.basescan.org/tx/0x84fa34de0a01a91a6da55bba71de60d0dcfbf6b1a1d41d4dd5ffb0d4403e1fbe)
- Member A round approval: [`0x9b20e79c199158f901c8d7dc8f641f9ddc63e17f8023438b9598534a6a079687`](https://sepolia.basescan.org/tx/0x9b20e79c199158f901c8d7dc8f641f9ddc63e17f8023438b9598534a6a079687)
- Member B round approval: [`0xb7bcfa8a3c7939c4f273e7c0165fa0745f1efecabbe252cea020b2d169249cf3`](https://sepolia.basescan.org/tx/0xb7bcfa8a3c7939c4f273e7c0165fa0745f1efecabbe252cea020b2d169249cf3)
- Member A contribution: [`0xc659a55f3df5f8defb97e4f631cdcc3d83944aa26cda35f39d7c8c52f4a922ed`](https://sepolia.basescan.org/tx/0xc659a55f3df5f8defb97e4f631cdcc3d83944aa26cda35f39d7c8c52f4a922ed)
- Member B contribution: [`0xc5a0cfd14db23e903e812c29ac5bcc29a503c0482c53226b1c6801b64f014794`](https://sepolia.basescan.org/tx/0xc5a0cfd14db23e903e812c29ac5bcc29a503c0482c53226b1c6801b64f014794)
- Settlement: [`0xbe77fd59264ac77b9c57d6438b6c5df24341150d98f2da45a65ff1b1388ec1c5`](https://sepolia.basescan.org/tx/0xbe77fd59264ac77b9c57d6438b6c5df24341150d98f2da45a65ff1b1388ec1c5)

Verified after settlement:

- round status is `Settled` (`4`);
- recorded contributions are exactly `250000` and `750000`;
- `consumedObligations(digest)` is `true`;
- merchant USDC balance increased to exactly `1000000` raw units for this test.

## Round 2 — unanimous cancellation and claims

- Obligation digest: `0x5d4aa38b0c141b37f41d6451ec2a406f0f25ca9e4a4a089b66ba67b1411d03fd`
- Create: [`0x821810296cf33e414ad95da4e98ece71e5415f505782f4c2c949b169905d0d6a`](https://sepolia.basescan.org/tx/0x821810296cf33e414ad95da4e98ece71e5415f505782f4c2c949b169905d0d6a)
- Member A cancellation request: [`0xed9a267f6abe6a0321c01dbc48e98822260f2e4a911ea74918057ec93238d5a2`](https://sepolia.basescan.org/tx/0xed9a267f6abe6a0321c01dbc48e98822260f2e4a911ea74918057ec93238d5a2)
- Member B cancellation request: [`0x0c09976d934d0e75876de7a93ffe53366725fbf50814baa394963acadb67879f`](https://sepolia.basescan.org/tx/0x0c09976d934d0e75876de7a93ffe53366725fbf50814baa394963acadb67879f)
- Member A refund claim: [`0xf1b96bd0426ccac590f365ac52f554cd3ec862196a42a8f6d40da7e641ece353`](https://sepolia.basescan.org/tx/0xf1b96bd0426ccac590f365ac52f554cd3ec862196a42a8f6d40da7e641ece353)
- Member B refund claim: [`0xc9b1da7731784d9e4c8184e0dc4037c3f0ffe5629f57af6549afc47c7ce6284e`](https://sepolia.basescan.org/tx/0xc9b1da7731784d9e4c8184e0dc4037c3f0ffe5629f57af6549afc47c7ce6284e)

Verified after both claims:

- round status is `Cancelled` (`5`);
- both recorded contribution claims are zero;
- PoolRound holds zero USDC;
- all five critical receipts (deployment, settlement, final cancellation, refund A, refund B) report success.
