import json
from collections.abc import Iterable
from enum import StrEnum
from functools import lru_cache
from typing import (
    Any,
    Awaitable,
    Callable,
    Literal,
    Optional,
    Sequence,
    Set,
    TypeVar,
    Union,
)

from pydantic import BaseModel
from pydantic.type_adapter import TypeAdapter
from redis.asyncio import Redis

from src.settings import settings

NULL_SENTINEL = "__NONE__"
"""Used to set the value when database return the value as None"""

T = TypeVar("T")


class CacheTag(StrEnum):
    USER = "tag:user"
    COURSE = "tag:course"
    MODULE = "tag:module"
    LESSON = "tag:lesson"
    ASSIGNMENT = "tag:assignment"
    ASSIGNMENT_SUBMISSION = "tag:assignment-submission"
    ENROLLMENT = "tag:enrollment"

    USER_ENTITY = "tag:user:{user_id}"
    COURSE_ENTITY = "tag:course:{course_id}"
    MODULE_ENTITY = "tag:module:{module_id}"
    LESSON_ENTITY = "tag:lesson:{lesson_id}"
    ASSIGNMENT_ENTITY = "tag:assignment:{assignment_id}"
    ASSIGNMENT_SUBMISSION_ENTITY = (
        "tag:assignment-submission:{assignment_submission_id}"
    )
    ENROLLMENT_ENTITY = "tag:enrollment:{enrollment_id}"

    LIST_USERS = "tag:list:users"
    LIST_COURSES = "tag:list:courses"
    LIST_ENROLLMENTS = "tag:list:enrollments"
    LIST_TRAINEES = "tag:list:trainees:{course_id}"

    LIST_MODULES = "tag:list:modules:{course_id}"
    LIST_LESSONS = "tag:list:lessons:{module_id}"
    LIST_ASSIGNMENT_SUBMISSIONS = "tag:list:assignment-submissions:{assignment_id}"

    SEARCH_USERS = "tag:search:users"
    SEARCH_COURSES = "tag:search:courses"

    # Dashboard
    ADMIN_KPIS = "tag:admin:dashboard:kpis"
    ADMIN_TOP_ENROLLED_COURSES = "tag:admin:top-enrolled-courses"
    TRAINEE_ENROLLED_COURSES = "tag:trainee:enrolled-courses:{trainee_id}"
    TRAINEE_TOP_NEW_COURSES = "tag:trainee:top-new-courses"
    TRAINEE_CURRENT_COURSE = "tag:trainee:current-course:{trainee_id}"
    TRAINER_ASSIGNED_COURSES = "tag:trainer:assigned-courses:{trainer_id}"
    TRAINER_KPIS = "tag:trainer:kpis:{trainer_id}"

    # Course Contents
    TRAINEE_COURSE_CONTENTS = "tag:trainee:course-contents:{course_id}"
    TRAINER_COURSE_CONTENTS = "tag:trainee:course-contents:{course_id}"

    # Assignment Contents
    TRAINEE_LIST_ASSIGNMENTS = "tag:trainee:list:assignments:{course_id}:{trainee_id}"
    TRAINER_LIST_ASSIGNMENTS = "tag:trainer:list:assignments:{course_id}"
    TRAINEE_ASSIGNMENT_CONTENTS = (
        "tag:trainee:assignment-contents:{assignment_id}:{trainee_id}"
    )
    TRAINER_ASSIGNMENT_CONTENTS = "tag:trainer:assignment-contents:{assignment_id}"

    # Course Overview
    TRAINEE_COURSE_OVERVIEW = "tag:trainee:course-overview:{course_id}"
    TRAINER_COURSE_OVERVIEW = "tag:trainer:course-overview:{course_id}"


class CacheKey(StrEnum):
    ADMIN_DASHBOARD_KPIS = "dashboard:admin:kpis"
    ADMIN_DASHBOARD_TOP_ENROLLED_COURSES = "dashboard:admin:top-enrolled-courses:{n}"
    TRAINEE_DASHBOARD_CURRENT_COURSE = "dashboard:trainee:current-course:{trainee_id}"
    TRAINEE_DASHBOARD_ENROLLED_COURSES = (
        "dashboard:trainee:enrolled-courses:{trainee_id}"
    )
    TRAINEE_DASHBOARD_TOP_NEW_COURSES = "dashboard:trainee:top-new-courses:{n}"
    TRAINER_DASHBOARD_KPIS = "dashboard:trainer:kpis:{trainer_id}"
    TRAINER_DASHBOARD_ASSIGNED_COURSES = (
        "dashboard:trainer:assigned-courses:{trainer_id}"
    )

    # Course Contents
    TRAINEE_COURSE_CONTENTS = "course-contents:trainee:{course_id}"
    TRAINER_COURSE_CONTENTS = "course-contents:trainer:{course_id}"

    # Course Overview
    TRAINEE_COURSE_OVERVIEW = "course-overview:trainee:{course_id}"
    TRAINER_COURSE_OVERVIEW = "course-overview:trainer:{course_id}"

    # Assignments
    TRAINEE_LIST_ASSIGNMENTS = "list:assignments:trainee:{course_id}:{trainee_id}"
    TRAINER_LIST_ASSIGNMENTS = "list:assignments:trainer:{course_id}"

    TRAINEE_ASSIGNMENT_CONTENTS = (
        "assignment-contents:trainee:{assignment_id}:{trainee_id}"
    )
    TRAINER_ASSIGNMENT_CONTENTS = "assignment-contents:trainer:{assignment_id}"

    # Assignment Submissions
    TRAINER_LIST_ASSIGNMENT_SUBMISSIONS = (
        "list:assignment-submissions:trainer:{assignment_id}:filters:"
        "from_date={from_date}&&to_date={to_date}&&status={status}&&sort_by_grade={sort_by_grade}"
        "page_meta:page={page}&&limit={limit}"
    )

    # List Entites.
    LIST_COURSES = (
        "list:courses:filters:course_name_or_trainer_name={course_name_or_trainer_name}&&"
        "sort_by_course_name={sort_by_course_name}&&"
        "sort_by_created_at={sort_by_created_at}&&"
        "sort_by_no_of_trainees={sort_by_no_of_trainees}"
        "page_meta:page={page}&&limit={limit}"
    )
    LIST_MODULES = "list:modules:{course_id}"
    LIST_LESSONS = "list:lessons:{module_id}"
    LIST_TRAINEES = (
        "list:trainees:{course_id}:filters:"
        "name={name}&&role={role}&&sort_by_enrollment_date={sort_by_enrollment_date}&&sort_by_username={sort_by_username}"
        "page_meta:page={page}&&limit={limit}"
    )
    LIST_ENROLLMENTS = (
        "list:enrollments:filters:"
        "name_or_email={name_or_email}&&status={status}&&role={role}&&"
        "sort_by_enrollment_date={sort_by_enrollment_date}&&"
        "sort_by_course_name={sort_by_course_name}"
        "page_meta:page={page}&&limit={limit}"
    )

    LIST_USERS = (
        "list:users:filters:"
        "name_or_email={name_or_email}&&role={role}&&"
        "sort_by_created_at={sort_by_created_at}&&sort_by_username={sort_by_username}"
        "page_meta:page={page}&&limit={limit}"
    )

    SEARCH_USERS = (
        "search:users:filters:username_or_email={username_or_email}&&role={role}"
    )

    SEARCH_COURSES = "search:courses:course_name={course_name}"


@lru_cache
def get_adapter(model: type[T]) -> TypeAdapter[T]:
    return TypeAdapter(model)


class CacheGet[T](BaseModel):
    """
    Datastructure to get a cache value.
    """

    key: str
    """Redis Key to get a value."""
    model: Any
    """Type to convert the json string into Python object"""


class CacheSet(BaseModel):
    """
    Datastructure to set a cache value.
    """

    key: str
    """Redis key to set a value."""
    value: Union[BaseModel, Sequence[BaseModel], None]
    """Value to store in a Redis key."""
    ttl: Optional[int] = None
    """Time to Live to add a expire time of a key in seconds"""
    tags: Optional[Set[Union[str, StrEnum]]] = None
    """
    Set of string used to group the keys, used to easily delete different keys,
    that belongs to the any one of the tag.
    """


class CacheService:
    def __init__(self) -> None:
        self._pool: Optional[Redis] = None

    async def init_pool(self) -> None:
        """
        Initalize the redis connection pool.
        """
        try:
            if self._pool is None:
                self._pool = Redis.from_url(
                    str(settings.redis.uri), decode_responses=True, db=0
                )

                print("Redis connection pool initalized successfully.")

        except Exception as e:
            print("Error occured while initalizing redis pool.")
            print(str(e))
            raise e

    async def close_pool(self) -> None:
        """
        close the redis connection pool.
        """
        if self._pool is None:
            raise RuntimeError("Redis connection pool not initialized to close.")

        await self._pool.aclose()
        self._pool = None
        print("Redis connection pool closed successfully.")

    @property
    def pool(self) -> Redis:
        """Returns the initalized connection pool."""
        if self._pool is None:
            raise RuntimeError("Redis connection pool not initialized!")
        return self._pool

    async def get(
        self, cache_obj: CacheGet[T]
    ) -> Union[T, list[T], None, Literal["__NONE__"]]:

        value = await self.pool.get(cache_obj.key)

        # If redis return None means, the key expires. and the service
        # will call database to get a value.
        if value is None:
            return None

        # If redis key has null sentinel value, service layer will
        # decide what to do with that.
        if value == NULL_SENTINEL:
            return NULL_SENTINEL

        adapter = get_adapter(cache_obj.model)
        # Convert the json like string into python object.
        value = json.loads(value)

        if adapter is not None:
            return adapter.validate_python(value)
        return value

    async def set(self, cache_obj: CacheSet) -> None:

        value = cache_obj.value

        if value is None:
            await self.pool.set(cache_obj.key, NULL_SENTINEL, ex=cache_obj.ttl)
            return

        if isinstance(value, list):
            value = [v.model_dump(mode="json") for v in value]
        elif isinstance(value, BaseModel):
            value = value.model_dump(mode="json")

        # Serialize to json.
        serialized_value = json.dumps(value)

        # Store in redis.
        await self.pool.set(cache_obj.key, serialized_value, ex=cache_obj.ttl)

        # Handle tags.
        if cache_obj.tags:
            pipe = self.pool.pipeline()

            for tag in cache_obj.tags:
                pipe.sadd(tag, cache_obj.key)

            await pipe.execute()

    async def invalidate_key(self, key: str) -> None:
        """Invalidate a single key."""
        await self.pool.delete(key)

    async def invalidate_tag(self, tag: Union[str, StrEnum]) -> None:
        keys: set[str] = await self.pool.smembers(tag)  # type: ignore
        # Invalidate all the keys associated with the tag.
        if keys:
            await self.pool.delete(*keys)
        # Delete the actual tag.
        await self.pool.delete(tag)

    async def invalidate_tags(self, tags: Iterable[Union[str, StrEnum]]) -> None:
        pipe = self.pool.pipeline()

        # Step 1: fetch all keys in pipeline
        for tag in tags:
            pipe.smembers(str(tag))

        results = await pipe.execute()

        # Step 2: delete keys + tags in pipeline
        pipe = self.pool.pipeline()
        for tag, keys in zip(tags, results):
            if keys:
                for key in keys:
                    print("--" * 50)
                    print(f"Invalidating key: {key}")
                pipe.delete(*keys)
            else:
                print("--" * 50)
                print(f"Invalidating tag {tag} with no keys")
            pipe.delete(str(tag))

        await pipe.execute()

    async def get_or_set(
        self,
        *,
        key: str,
        model: Any,
        fetch_func: Callable[[], Awaitable[T]],
        tags: Optional[Set[Union[str, StrEnum]]] = None,
        ttl: Optional[int] = None,
        negative_ttl: Optional[int] = None,
    ) -> T:
        """
        Get value from cache. If not present, fetch using fetch_func,
        store in cache, and return the value.
        """

        # 1. Try cache
        cached = await self.get(CacheGet(key=key, model=model))

        # Cache hit
        if cached is not None:
            if cached == NULL_SENTINEL:
                return None  # type: ignore
            return cached  # type: ignore

        # 2. Cache miss → fetch from source
        value: T = await fetch_func()

        # 3. Decide TTL (normal vs negative caching)
        if value is None:
            ttl_to_use = negative_ttl
        else:
            ttl_to_use = ttl

        # 4. Store in cache
        await self.set(
            CacheSet(
                key=key,
                value=value,  # type: ignore
                ttl=ttl_to_use,
                tags=tags,
            )
        )

        # 5. Return fresh value
        return value
