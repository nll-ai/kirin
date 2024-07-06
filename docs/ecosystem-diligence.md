# Things I've looked at

## Content-Addressed Storage

- [`hashfs`](https://github.com/dgilland/hashfs)
  - Package appears unmaintained, with the last commit being 5 years ago from 6 July 2024.
- [`s3-cas`](https://github.com/nuchi/s3-cas)
  - Unmaintained?
  - Super tailored to s3, not flexible.
  - Seems good for learning.
- Alternative is to roll it on our own, which is what we do right now.
  - However, current implementation lacks a more efficient tree structure that hashfs has.
  - This can be found [here](https://github.com/dgilland/hashfs/blob/ee8c523e8edacccf643d68cb4e033fb740941a44/hashfs/utils.py#L19)
  - Files are stored in one directory.
