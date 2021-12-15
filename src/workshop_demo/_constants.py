SEQ_REGEX = r"(.*)/([0-9]{2,})$"
GT_REGEX = r"(.*)/([0-9]{2,})(_(?:GT|AUTO))/SEG$"

SEQ_TIF_REGEX = rf'{SEQ_REGEX[:-1]}/t([0-9]{{3}}){"."}tif$'
GT_TIF_REGEX = rf'{GT_REGEX[:-1]}/(?:man_)?seg([0-9]{{3}}){"."}tif$'
