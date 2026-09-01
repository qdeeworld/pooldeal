---
version: alpha
name: PoolDeal validation journey
description: One continuous user-first flow that makes a remembered contribution obligation visibly change the next team purchase.
---

## Overview

PoolDeal serves a two-person onchain team preparing a repeat purchase. The interface must make one product truth immediately legible: one member covered an extra amount previously, so the signed remembered obligation reduces that member's next contribution. The primary journey is an operational validation surface, not a marketing site, architecture viewer, or evaluator dashboard.

## Layout

Use one linear workspace whose reading order matches the state transition: prior agreement, process restart, recalled split, wallet approvals, settlement, and consumption. Keep the flat 50/50 comparison adjacent to the recalled 25/75 proposal so the memory-caused difference is visible without narration. Keep Base receipts contextual to the action that produced them instead of moving proof into separate navigation.

At narrow widths, preserve the same order and show each member's old and new amount together. Do not place technical logs before the decision difference.

## Components

The primary action changes with the workflow state and must name the immediate user outcome. Memory status must distinguish written, process stopped, recalled, refused, and consumed states. Wallet controls must show the connected address, Base Sepolia network, exact approved amount, pending state, success receipt, rejection, and retry path.

Failure states must keep cancellation and refund actions available from onchain state when Sibyl is missing or invalid. Recalled human notes are display-only and must never be styled as executable instructions or authority.

## Do's and Don'ts

Do show `50/50 → 25/75` as the focal moment. Do visibly expose the fresh process and session identifiers. Do use the ordinary user journey for verification.

Don't preload session two, accept a caller-selected tenant, silently fall back to an equal split, hide the write or restart, or require logs to understand why the contribution changed. Don't add Virtuals, a marketplace, generalized treasury controls, token design, or judge-only navigation to this release.
