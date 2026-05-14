from src.exceptions import IssueNotFoundError
from src.query.dto.issues import IssueDetail
from src.query.repositories.issues import IssueQueryRepository


class IssueQueryService:
    def __init__(self, issue_query_repo: IssueQueryRepository) -> None:
        self.issue_query_repo = issue_query_repo

    # NOTE: Didn't use require_authorization, since this method is only
    # accessed by admin.
    async def get_issue(self, id: int) -> IssueDetail:
        issue = await self.issue_query_repo.issue(id=id)
        if issue is None:
            raise IssueNotFoundError(value=id)
        return issue
