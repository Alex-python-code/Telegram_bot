from app.async_models import async_session
from app.async_models import User
from sqlalchemy import case, update


async def set_users_activity(users: dict):
    async with async_session() as session:
        try:
            stmt = (
                update(User)
                .where(User.tg_id.in_(users.keys()))
                .values(
                    last_activity=case(
                        *[(User.tg_id == k, v) for k, v in users.items()],
                        else_=User.last_activity,
                    )
                )
            )
            await session.execute(stmt)
            await session.commit()
            print("Всё записано")
            print(users)

        except Exception as e:
            return e

        return None
