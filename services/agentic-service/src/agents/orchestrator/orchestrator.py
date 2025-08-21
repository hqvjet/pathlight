from schemas.context import State

class Orchestrator:
    def __init__(self):
        pass

    def __call__(self, state: State) -> str:
        print("[Orchestrator] state:", state)

        # Require vars
        id = state.id
        difficulty = state.difficulty
        duration = state.duration
        s3_bucket = state.s3_bucket

        # Generated vars
        title = state.title
        description = state.description
        roadmap = state.roadmap
        lessons = state.lessons
        final_test = state.final_test

        if not id or not difficulty or not duration:
            raise ValueError("ID, Difficulty, Duration, and S3 Bucket are required in the state.")

        elif not title and not description and not roadmap:
            print('Using Planner Agent')
            return 'create_plan'
        # elif not lessons:
        #     print('Using Lesson Creator Agent')
        #     return 'create_lesson'
        # elif not final_test:
        #     print('Using Final Test Creator Agent')
        #     return 'create_final_test'
        else:
            return 'done'
