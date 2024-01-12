# DICOM to MinIO

Script to upload directories of DICOM files to MinIO.

Requires:

-   Python
-   MinIO `mc` client
-   gzip

Directory format must be `<prefix>/<YYYY>/<MM>/<DD>/<AccessionNumber>/`, e.g., `/PACS/2017/05/28/ABCD`.
