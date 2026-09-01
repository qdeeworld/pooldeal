# Base Sepolia validation — 2026-09-01

Evidence level: E2 observable replay. These transactions were founder-operated through the CLI. They prove public contract behavior, not independent use, PMF, or a judge-completable public product.

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
