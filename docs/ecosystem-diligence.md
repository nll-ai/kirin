# Things I've looked at

## Content-Addressed Storage

- [`hashfs`](https://github.com/dgilland/hashfs)
  - Package appears unmaintained, with the last commit being 5 years ago from 6 July 2024.
- [`s3-cas`](https://github.com/nuchi/s3-cas)
  - Unmaintained?
  - Super tailored to s3, not flexible.
  - Seems good for learning.
- Alternative is to roll it on our own, which is what we do right now.
  - However, current implementation lacks a more efficient tree structure.
  - Files are stored in one directory.
