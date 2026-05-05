import aiosqlite
from utils.utilities import aprint, database_path

class SQLiteHandler:
    @staticmethod
    async def check_tables() -> None:
        checkTeamsTableQuery = 'select Name from Teams;'
        checkRequestsTableQuery = 'select UserId from Requests;'
        checkSubmissionsTableQuery = 'select Team from Submissions;'

        teamsTableCreationQuery = 'create table Teams (Name varchar(255) not null, Leader int not null, Members varchar(255) default null, primary key (Name));'
        requestsTableQuery = 'create table Requests (UserId int not null, Team varchar(255) not null);'
        submissionsTableQuery = 'create table Submissions (Team str not null, GameId int not null, Title str not null, URL str not null, primary key (Team));'

        async with aiosqlite.connect(database_path) as db:
            try: await db.execute(checkTeamsTableQuery)
            except:
                await db.execute(teamsTableCreationQuery)
                await db.commit()
            finally:
                try:
                    await db.execute(checkRequestsTableQuery)
                except:
                    await db.execute(requestsTableQuery)
                    await db.commit()
                finally:
                    try: await db.execute(checkSubmissionsTableQuery)
                    except:
                        await db.execute(submissionsTableQuery)
                        await db.commit()
                    finally:
                        await aprint("Tables are properly registered in the database!")

    @staticmethod
    async def create_team(team: str, leader_id: int) -> None:
        teamExistsQuery = f'select case when exists (select Name from Teams where Name="{team}") then true else false end;'
        registerTeamQuery = f'insert into Teams (Name, Leader) values ("{team}", {leader_id})'

        async with aiosqlite.connect(database_path) as db:
            async with db.execute(teamExistsQuery) as cursor:
                row = await cursor.fetchone()
                if row[0] == 0:
                    await db.execute(registerTeamQuery)
                    await db.commit()

    @staticmethod
    async def transfer_team_leadership(team: str) -> None:
        members = await SQLiteHandler.get_team_total_members(team)
        old_leader = members.pop(0)

        leader = members[0] # new leader
        members.pop(0) #remove him to form the members string
        members.append(old_leader)
        fixed_list = list()
        for member in members:
            fixed_list.append(str(member))
        member_string = ','.join(fixed_list)

        async with aiosqlite.connect(database_path) as db:
            await db.execute(f'update Teams set Leader={leader}, Members="{member_string}" where Name="{team}";')
            await db.commit()

    @staticmethod
    async def delete_team(team: str) -> None:
        deleteTeamQuery = f'delete from Teams where Name="{team}";'
        deleteRemainingRequestsQuery = f'delete from Requests where Team="{team}";'

        async with aiosqlite.connect(database_path) as db:
            await db.execute(deleteTeamQuery)
            await db.execute(deleteRemainingRequestsQuery)
            await db.commit()

    @staticmethod
    async def get_all_teams() -> dict:
        infoGatheringQuery = 'select Name from Teams;'
        result = dict()

        async with aiosqlite.connect(database_path) as db:
            async with db.execute(infoGatheringQuery) as cursor:
                rows = await cursor.fetchall()

                for row in rows:
                    team: str = row[0]
                    total_members = await SQLiteHandler.get_team_total_members(team)
                    result[team] = total_members

        return result

    @staticmethod
    async def get_team_total_members(team: str) -> list:
        infoGatheringQuery = f'select Leader, Members from Teams where Name="{team}";'
        members = list()

        async with aiosqlite.connect(database_path) as db:
            async with db.execute(infoGatheringQuery) as cursor:
                row = await cursor.fetchone()

                members.append(row[0]) # the leader is always there...
                if row[1] is not None and row[1] != '':
                    member_list = row[1].split(",")

                    fixed_list = list()
                    for member in member_list:
                        if member != '': fixed_list.append(int(member))
                    members.extend(fixed_list)

        return members

    @staticmethod
    async def is_user_on_any_team(user_id: int) -> bool:
        checkQuery = f'select Leader, Members from Teams;'
        result: bool = False

        async with aiosqlite.connect(database_path) as db:
            async with db.execute(checkQuery) as cursor:
                rows = await cursor.fetchall()

                for row in rows:
                    leader, members = row
                    if members is not None: member_list = members.split(",")
                    else: member_list = []

                    if user_id != leader and not str(user_id) in member_list: continue
                    else: result = True; break

        return result

    @staticmethod
    async def get_team_by_member(user_id: int) -> str:
        teams = await SQLiteHandler.get_all_teams()
        result = ''

        for team, members in teams.items():
            if user_id in members:
                result = team
                break

        return result

    @staticmethod
    async def team_exists(team_name: str) -> list:
        all_teams = await SQLiteHandler.get_all_teams()
        teams = list(all_teams.keys())
        fixed_teams = list()
        for team_c in teams:
            fixed_teams.append(team_c.lower())
        if team_name.lower() in fixed_teams: return [True, teams[fixed_teams.index(team_name.lower())]]
        else: return [False, None]

    @staticmethod
    async def add_user_to_team(team: str, user_id: int) -> None:
        membersStringQuery = f'select Members from Teams where Name="{team}";'

        async with aiosqlite.connect(database_path) as db:
            cursor = await db.execute(membersStringQuery)
            row = await cursor.fetchone()
            members: str | None = row[0]

            if members is not None:
                member_list = members.split(",")
                member_list.append(str(user_id))

                final_members_string = ','.join(member_list)
                await db.execute(f'update Teams set Members="{final_members_string}" where Name="{team}";')
                await db.commit()
            else:
                await db.execute(f'update Teams set Members="{str(user_id)}" where Name="{team}";')
                await db.commit()

            await cursor.close()

    @staticmethod
    async def remove_member_from_team(team: str, user_id: int) -> bool:
        membersStringQuery = f'select Members from Teams where Name="{team}";'
        result = True

        async with aiosqlite.connect(database_path) as db:
            async with db.execute(membersStringQuery) as cursor:
                row = await cursor.fetchone()
                members_string: str = row[0]

                if members_string is not None:
                    members_list = members_string.split(',')
                    if str(user_id) in members_list:
                        members_list.remove(str(user_id))
                        final_members_string = ','.join(members_list)
                        if len(final_members_string) != 0:
                            await db.execute(f'update Teams set Members="{final_members_string}" where Name="{team}";')
                        else:
                            await db.execute(f'update Teams set Members=NULL where Name="{team}";')
                        await db.commit()
                    else: result = False
                else: result = False

        return result

    @staticmethod
    async def create_team_request(team: str, user_id: int) -> int:
        request_exists = await SQLiteHandler.request_exists(team, user_id)
        requestCreationQuery = f'insert into Requests values ({user_id}, "{team}");'

        async with aiosqlite.connect(database_path) as db:
            if len(await SQLiteHandler.get_team_total_members(team)) >= 4: result = -1  # team is full
            elif not request_exists:
                await db.execute(requestCreationQuery)
                await db.commit()
                result = 1
            else: result = 0

        return result #all ended well...

    @staticmethod
    async def dismiss_team_request(team: str, user_id: int) -> None:
        deletionQuery = f'delete from Requests where UserId={user_id} and Team="{team}";'

        async with aiosqlite.connect(database_path) as db:
            await db.execute(deletionQuery)
            await db.commit()

    @staticmethod
    async def dismiss_all_team_requests(team: str) -> None:
        deletionQuery = f'delete from Requests where Team="{team}";'

        async with aiosqlite.connect(database_path) as db:
            await db.execute(deletionQuery)
            await db.commit()

    @staticmethod
    async def dismiss_all_user_requests(user_id: int) -> None:
        deletionQuery = f'delete from Requests where UserId="{user_id}";'

        async with aiosqlite.connect(database_path) as db:
            await db.execute(deletionQuery)
            await db.commit()

    @staticmethod
    async def get_team_total_requests(team: str) -> list:
        infoGatheringQuery = f'select UserId from Requests where Team="{team}";'
        requests = list()

        async with aiosqlite.connect(database_path) as db:
            async with db.execute(infoGatheringQuery) as cursor:
                rows = await cursor.fetchall()

                for row in rows:
                    if row is None: break
                    if row[0] is not None: requests.append(row[0])

        return requests

    @staticmethod
    async def request_exists(team: str, user_id: int) -> bool:
        requested_users = await SQLiteHandler.get_team_total_requests(team)
        if user_id in requested_users: return True
        return False
    
    @staticmethod
    async def submit_game(team: str, game_name: str, game_url: str, game_id: int) -> None:
        insertSubmission = f'insert or replace into Submissions values ("{team}", {game_id}, "{game_name}", "{game_url}")'

        async with aiosqlite.connect(database_path) as db:
            await db.execute(insertSubmission)
            await db.commit()

    @staticmethod
    async def clear_submissions() -> None:
        async with aiosqlite.connect(database_path) as db:
            await db.execute("delete from Submissions;")
            await db.commit()

    @staticmethod
    async def gather_submissions() -> list:
        async with aiosqlite.connect(database_path) as db:
            cursor = await db.execute("select * from Submissions;")
            print(cursor)

        return list()

class JSONHandler:
    @staticmethod
    async def submit_vote() -> None:
        pass

    @staticmethod
    async def get_voted_game() -> object: #change return type
        pass

    @staticmethod
    async def get_all_votes() -> object:
        pass