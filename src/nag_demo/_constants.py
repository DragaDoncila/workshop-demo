SEQ_REGEX = r'(.*)/([0-9]{2,})$'
GT_REGEX = r'(.*)/([0-9]{2,})_GT/SEG$'

SEQ_TIF_REGEX = rf'{SEQ_REGEX[:-1]}/t([0-9]{{3}}){"."}tif$'
GT_TIF_REGEX = rf'{GT_REGEX[:-1]}/man_seg([0-9]{{3}}){"."}tif$'
