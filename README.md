# IIIF Presentation API

CRKN module

## Table of Contents

1. [Description](#description)
1. [Usage - Configuration options and additional functionality](#usage)
1. [Limitations - OS compatibility, etc.](#limitations)
1. [Development - Guide for contributing to the module](#development)

## Description

This API allows users to upload a IIIF manifest.json file to Swift containers and retrieve a manifest.json file by searching for a manifest ID.

## Usage

This module is used as the backend for the Digirati editor: https://github.com/crkn-rcdr/crkn-digirati-editor.

## Limitations

The uploaded manifest.json file must comply with the IIIF Presentation API requirements. The API includes a manifest.json validator from https://presentation-validator.iiif.io/.

## Development

The functionality of upload is udes only by CRKN.
