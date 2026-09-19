# Dataset artifact directory migration

The user requested a descriptive directory name. Active dataset files now live in `results/dataset_reconstruction/`; the previous name was `results/task1/`. The directory was moved intact and maintained source, tests, documentation and explorer links were updated.

No raw input, annotation, label, feature value, fold assignment or prediction changed. Dataset TSV files, features.tsv, folds.tsv and predictions.tsv remain byte-for-byte identical. One model reproduction refreshed the code provenance after its default input path changed; every scientific metric is exactly equal, and model_code_sha256 is the only changed metrics field. See path_migration_verification.json for old/new hashes.

Historical execution logs and literal executed commands are retained unchanged. Any old dataset path inside such a snapshot records the location at execution time; substitute the new directory when reproducing it now. Historical review and classifier metric snapshots are retained under history/. The original metric hash cited in the GPU review is historical, with its current successor recorded in final_review_verification.json.

The dataset manifest references source files and output basenames, so the existing source and output checksum records remain valid after this move. Contact and GPU matching inputs retain exactly the same bytes and checksums; those analyses do not require rerunning for a path change.
