# Missing-crop source audit for the 70-case collision study

Among the 70 frozen residual cases, 29 contain one or more compatible competitors without a computable screenshot crop. This targeted diagnostic identifies why those 84 competing crops are unavailable, using the same released DMR candidate documents and the same replay-linked screenshots.

Classify each compatible, missing-crop competitor using the originally published `[[bbox]]` field and the replay screenshot dimensions:

1. `bbox_absent`: no usable bounding-box field in the candidate document
2. `bbox_incomplete`: missing one or more of x, y, width or height
3. `bbox_too_small`: width or height is 2 pixels or less, as screened by the original parser
4. `bbox_clipped_below_three`: parsing succeeds but clipping to screenshot dimensions leaves fewer than three pixels in width or height

The categories are exclusive. Successful screenshot downloads and the existence of a target screenshot are prerequisites. For every missing-crop competitor, the category must agree with the original `crop_hash` availability rule. The total must reconcile to the 84 missing-crop competitors already recorded across the 29 affected actions.

The output includes category counts and public demo/turn keys only. No screenshot, URL, raw attribute, locator or text content will be exported. This is a source-evidence diagnosis of crop availability, without inferring the cause of the recorded bounding-box values.
