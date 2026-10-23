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
        return fmt_number(float(value)*100,decimals)+"%" 
    except (TypeError,ValueError,OverflowError):
        return "—"

