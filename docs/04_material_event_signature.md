# Material Event Signature

Material Event Signature means: a measured, time-bounded, physically grounded response from a material object under a defined challenge.

## What it is not
- Not simply a private key.
- Not simply an image or decorative fingerprint.
- Not a legal certificate.

## What it connects
A Material Event Signature is an evidence object connecting:
- material object,
- measurement challenge,
- response data,
- feature vector,
- hash,
- optional signature,
- optional ledger anchor.

```text
[Material Object]
       |
       v
[Defined Challenge] ---> [Measured Response Data]
                               |
                               v
                        [Feature Vector]
                               |
                               v
                           [Data Hash]
                               |
               +---------------+----------------+
               |                                |
               v                                v
       [Optional Signature]            [Optional Ledger Anchor]
               \                                /
                \                              /
                 +----> [Material Event Signature Evidence]
```
