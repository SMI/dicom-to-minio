# DICOM to MinIO

Script to upload directories of DICOM files to MinIO.

Requires:

-   Python
-   MinIO `mc` client
-   gzip

Features:

-   Compresses each directory on upload. Compression level is configurable (default `gzip -9`)
-   Adds useful object metadata:
    ```json
    {
        "Content-Type": "application/gzip",
        "X-Amz-Meta-Content-Md5": "8b0dcc24439db3359bdd926f025aa635",
        "X-Amz-Meta-Modalities": "CT,SR",
        "X-Amz-Meta-Total-Count": "4"
    }
    ```
-   Verify checksum of existing objects, and `--overwrite` if specified

Directory format must be `<prefix>/<YYYY>/<MM>/<DD>/<AccessionNumber>/`, e.g., `/PACS/2017/05/28/ABCD`.
