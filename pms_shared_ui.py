"""PMS shared visual primitives — same source in Bersoch and DEMO."""
def style_bar(fig, horizontal=True):
    """Compact financial bar chart, transparent background and consistent axes."""
    fig.update_traces(marker_line_width=1.6, marker_line_color="rgba(231,240,250,0.52)", opacity=0.96)
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font_color="#dce6f2", bargap=0.42, barcornerradius=5,
        margin=dict(l=8,r=46,t=12,b=12), legend_title_text="")
    if horizontal:
        fig.update_yaxes(title_text=None, showgrid=False, categoryorder="total ascending")
        fig.update_xaxes(gridcolor="rgba(170,193,214,0.12)", zeroline=False)
    return fig

def fmt_number(value, decimals=0):
    import math
    try:
        n=float(value)
        if not math.isfinite(n):
            return "—"
        return f"{n:,.{decimals}f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except (TypeError,ValueError,OverflowError):
        return "—"

def fmt_usd(value):
    formatted=fmt_number(value)
    return "US$ "+formatted if formatted!="—" else formatted

def fmt_pct_fraction(value, decimals=1):
    try:
        formatted=fmt_number(float(value)*100,decimals)
        return formatted+"%" if formatted!="—" else "—" 
    except (TypeError,ValueError,OverflowError):
        return "—"


def render_financial_table(st, frame, *, row_height=36):
    """Uniform financial table for the two cockpit adapters."""
    return st.dataframe(frame, hide_index=True, width="stretch", row_height=row_height)

def render_kpi_card(st, label, value, sub=""):
    """Escaped labels prevent markup injection from external portfolio data."""
    from html import escape
    return st.markdown(
        '<div class="demo-card"><div class="demo-label">'+escape(str(label))+
        '</div><div class="demo-value">'+escape(str(value))+
        '</div><div class="demo-small">'+escape(str(sub))+'</div></div>',
        unsafe_allow_html=True)
