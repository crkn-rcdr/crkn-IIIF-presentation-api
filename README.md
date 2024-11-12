# IIIF Presentation API

CRKN module

## Table of Contents

1. [Description](#description)
2. [Usage - Configuration options and additional functionality](#usage)
3. [Limitations - OS compatibility, etc.](#limitations)
4. [Development - Guide for contributing to the module](#development)

## Description

This API allows users to upload a IIIF manifest.json file to Swift containers and retrieve a manifest.json file by searching for a manifest ID.

## Usage

This module is used as the backend for the Digirati editor: https://github.com/crkn-rcdr/crkn-digirati-editor.

## Limitations

The uploaded manifest.json file must comply with the IIIF Presentation API requirements. The API includes a manifest.json validator from https://presentation-validator.iiif.io/.

## Development

The upload functionality is used only by CRKN, while the data retrieval functionality is open to the public.
