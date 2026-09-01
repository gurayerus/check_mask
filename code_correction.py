
    # code snippet to select largest connected component in icv mask
    # was required to remove non brain small clusters
    if refaced_data:
        import SimpleITK as sitk

        for _, tmp_row in df_img.iterrows():
            img_prefix = tmp_row.img_prefix
            fpath = os.path.join(out_dir, img_prefix + SUFF_DLICV)
            if os.path.exists(fpath):
                s2_dlicv_output = sitk.ReadImage(fpath)
                # Keep only the largest connected component
                mask_component = sitk.ConnectedComponent(s2_dlicv_output)
                mask_sorted_component = sitk.RelabelComponent(
                    mask_component, sortByObjectSize=True
                )
                final_mask = sitk.Equal(mask_sorted_component, 1)
                # Write refined mask back in-place within s2_dlicv
                sitk.WriteImage(final_mask, fpath)

