"""
Pagination utilities for data display.
"""

import streamlit as st


def paginate_dataframe(df, page_size=20, page_key="page"):
    """Paginate dataframe for better performance."""
    if df.empty:
        return df, 1, 1

    total_pages = len(df) // page_size + (1 if len(df) % page_size else 0)

    if total_pages > 1:
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            page = st.selectbox(
                f"Page (showing {page_size} riders per page)",
                range(1, total_pages + 1),
                format_func=lambda x: f"Page {x} of {total_pages}",
                key=page_key,
                help=f"Navigate through {len(df)} riders",
            )
    else:
        page = 1

    start_idx = (page - 1) * page_size
    end_idx = min(start_idx + page_size, len(df))

    return df.iloc[start_idx:end_idx], page, total_pages
