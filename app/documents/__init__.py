"""Branded PDF documents: client quote, invoice and internal cost sheet.

Builders turn ORM records into plain `DocumentData`; the renderer turns
`DocumentData` into PDF bytes. The renderer never touches the database.
"""
