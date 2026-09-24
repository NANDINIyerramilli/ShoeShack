import arxiv

_client = arxiv.Client()


class _ArxivTool:
    def __init__(self, top_k: int = 3, summary_chars: int = 400):
        self.top_k = top_k
        self.summary_chars = summary_chars

    def run(self, query: str) -> str:
        search = arxiv.Search(
            query=query,
            max_results=self.top_k,
            sort_by=arxiv.SortCriterion.Relevance,
        )
        results = list(_client.results(search))
        if not results:
            return "No ArXiv results found."

        blocks = []
        for r in results:
            authors = ", ".join(a.name for a in r.authors[:3])
            if len(r.authors) > 3:
                authors += ", et al."
            summary = (r.summary or "").strip().replace("\n", " ")
            if len(summary) > self.summary_chars:
                summary = summary[: self.summary_chars].rstrip() + "…"
            published = r.published.strftime("%Y-%m-%d") if r.published else "n/a"
            blocks.append(
                f"Title: {r.title}\n"
                f"Authors: {authors}\n"
                f"Published: {published}\n"
                f"Link: {r.entry_id}\n"
                f"Summary: {summary}"
            )
        return "\n\n".join(blocks)


arxiv_tool = _ArxivTool()
