# dicoder
Developer assistant with dialog between an LLM and a code analyzer

This repository contains the scripts and dataset for "DiCoder: Iterative Code Completion" paper.

The `benchmark` directory contains the scripts and configuration files needed to run the evaluations.
The `coder` directory contains the implementation of DiCoder.
`server` allows running open source LLMs on a server so that DiCoder can use them through an API call.
