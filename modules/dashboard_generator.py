def generate_dashboard(accounts):

    rows = ""

    for _, row in accounts.sort_values(
        "overall_coi",
        ascending=False
    ).iterrows():

        rows += f"""
        <tr>
            <td>{row["overall_coi"]}</td>
            <td>{row["confidence"]}</td>
            <td>{row["priority"]}</td>
            <td>{row["Account Name"]}</td>
            <td>{row["industry"]}</td>
            <td>{row["business_model"]}</td>
        </tr>
        """

    html = f"""
    <html>
    ...
    {rows}
    ...
    """

    with open(
        "output/account_dashboard.html",
        "w"
    ) as f:

        f.write(html)
