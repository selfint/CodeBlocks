from pandas import DataFrame, Series


def get_depths(df: DataFrame, src_col: str, dst_col: str) -> Series:
    depths = Series(0, index=df.index)

    # find all roots as sources that are never a destination
    src_is_root = df[src_col].apply(lambda s: s not in df[dst_col].values)

    # no roots means everything is at the same depth
    if not src_is_root.any():
        return depths

    # get all depths of all non-root connections
    non_roots: DataFrame = df[~src_is_root]
    if not non_roots.empty:
        non_root_depths = get_depths(non_roots, src_col, dst_col)

        # update all depths of non root connections to be relative
        # to our roots
        non_root_depths += 1

        # update depths of non root connections
        depths.update(non_root_depths)

    return depths


