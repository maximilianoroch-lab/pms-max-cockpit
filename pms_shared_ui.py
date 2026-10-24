"""PMS shared visual primitives — same source in Bersoch and DEMO."""
def style_bar(fig, horizontal=True):
    """PMS Executive: restrained financial bars, consistent in both cockpits."""
    fig.update_traces(
        marker_line_width=1.2,
        marker_line_color="rgba(185,218,242,0.58)",
        opacity=0.96,
        textfont=dict(size=13,color="#e6eef8"),
        hoverlabel=dict(bgcolor="#13263c",font_size=13),
    )
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#dce6f2",size=13),
        bargap=0.48,
        barcornerradius=6,
        margin=dict(l=8,r=64,t=14,b=22),
        legend_title_text="",
        legend=dict(bgcolor="rgba(0,0,0,0)",font=dict(size=12)),
        hovermode="closest",
    )
    if horizontal:
        fig.update_yaxes(title_text=None,showgrid=False,categoryorder="total ascending",
                         ticks="",tickfont=dict(size=13,color="#dce6f2"))
        fig.update_xaxes(gridcolor="rgba(160,191,220,0.09)",gridwidth=1,
                         zeroline=False,ticks="",tickfont=dict(size=11,color="#9baec2"))
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

def finish_executive_bar(fig, *, stacked=False):
    """Final pass for corporate diversification and custody charts."""
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Arial, sans-serif",size=13,color="#dce6f2"),
        hoverlabel=dict(bgcolor="#10263b",bordercolor="#56738d",
                        font=dict(family="Arial, sans-serif",size=13,color="#f2f6fb")),
        bargap=0.38 if stacked else 0.51,
        barcornerradius=5,
        legend=dict(orientation="h",yanchor="top",y=-0.13,xanchor="left",x=0,
                    bgcolor="rgba(0,0,0,0)",font=dict(size=11,color="#b8c9da"),
                    title_text=""),
    )
    fig.update_xaxes(showline=False,zeroline=False,showgrid=True,
        gridcolor="rgba(145,173,197,0.09)",ticks="",tickfont=dict(size=11,color="#91a7bc"),
        title_font=dict(size=11,color="#a9c0d5"))
    fig.update_yaxes(showgrid=False,showline=False,ticks="",
        tickfont=dict(size=13,color="#e9f1f9"),title_text=None)
    return fig
