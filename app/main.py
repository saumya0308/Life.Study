from __future__ import annotations

import random
from datetime import datetime
from pathlib import Path

from fastapi import Depends, FastAPI, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from .db import Base, engine, get_db
from .game.engine import MAX_TORCHES, accuracy, mastery_from_attempts, resolve_answer
from .game.questions import QUESTIONS, TREASURES
from .models import GameSession, QuestionAttempt, SessionTreasure, Student

BASE_DIR = Path(__file__).resolve().parent

app = FastAPI(title="Jungle Ancient Ruin Adventure")
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=BASE_DIR / "templates")

Base.metadata.create_all(bind=engine)

ROOM_NAMES = [
    "Jungle Entrance",
    "Overgrown Gate",
    "Hall of Living Organisms",
    "Growth Gallery",
    "Reproduction Vault",
    "Chamber of Metabolism",
    "Cellular Sanctum",
    "Hall of Stimuli",
    "Biodiversity Passage",
    "Hall of Scientific Names",
    "Taxonomy Passage",
    "Hall of Hierarchy",
    "Museum Chamber",
    "Temple of Taxonomical Aids",
    "Final Ruin Chamber",
]

TREASURE_FACTS = [
    "Species is the basic unit of classification.",
    "Taxonomy includes identification, nomenclature and classification.",
    "Metabolism is the total sum of chemical reactions occurring in a living organism.",
    "A herbarium contains dried, pressed and preserved plant specimens.",
    "A pair of contrasting statements in a taxonomic key is called a couplet.",
    "The genus name begins with a capital letter in binomial nomenclature.",
]


def get_game(db: Session, game_id: int) -> GameSession:
    game = db.get(GameSession, game_id)
    if not game:
        raise HTTPException(status_code=404, detail="Game session not found")
    return game


def attempted_ids(game: GameSession) -> set[int]:
    return {attempt.question_id for attempt in game.attempts}


def difficulty_for_room(room: int, total: int) -> str:
    fraction = room / max(total, 1)
    if fraction <= 0.34:
        return "easy"
    if fraction <= 0.72:
        return "medium"
    return "hard"


def choose_question(game: GameSession):
    used = attempted_ids(game)
    target = difficulty_for_room(game.current_room, game.total_rooms)

    candidates = [
        item for item in QUESTIONS
        if item["id"] not in used and item["difficulty"] == target
    ]
    if not candidates:
        candidates = [item for item in QUESTIONS if item["id"] not in used]
    if not candidates:
        candidates = QUESTIONS[:]
    return random.choice(candidates)


def find_question(question_id: int):
    for item in QUESTIONS:
        if item["id"] == question_id:
            return item
    raise HTTPException(status_code=404, detail="Question not found")


@app.get("/", response_class=HTMLResponse)
def start_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="start.html",
        context={"max_torches": MAX_TORCHES},
    )


@app.post("/start")
def start_game(
    student_name: str = Form(...),
    db: Session = Depends(get_db),
):
    name = student_name.strip()[:120] or "Explorer"
    student = Student(name=name)
    db.add(student)
    db.flush()

    game = GameSession(
        student_id=student.id,
        torches_remaining=MAX_TORCHES,
        total_rooms=len(ROOM_NAMES),
    )
    db.add(game)
    db.commit()
    db.refresh(game)

    return RedirectResponse(url=f"/game/{game.id}", status_code=303)


@app.get("/game/{game_id}", response_class=HTMLResponse)
def game_page(
    request: Request,
    game_id: int,
    db: Session = Depends(get_db),
):
    game = get_game(db, game_id)

    if game.game_over or game.completed:
        return RedirectResponse(url=f"/game/{game.id}/results", status_code=303)

    question = choose_question(game)
    options = question["options"][:]
    random.shuffle(options)

    return templates.TemplateResponse(
        request=request,
        name="game.html",
        context={
            "game": game,
            "student": game.student,
            "question": question,
            "options": options,
            "room_name": ROOM_NAMES[game.current_room - 1],
            "max_torches": MAX_TORCHES,
        },
    )


@app.post("/game/{game_id}/answer", response_class=HTMLResponse)
def answer_question(
    request: Request,
    game_id: int,
    question_id: int = Form(...),
    selected_answer: str = Form(...),
    db: Session = Depends(get_db),
):
    game = get_game(db, game_id)
    if game.game_over or game.completed:
        return RedirectResponse(url=f"/game/{game.id}/results", status_code=303)

    question = find_question(question_id)
    if selected_answer not in question["options"]:
        raise HTTPException(status_code=400, detail="Invalid answer option")

    is_correct = selected_answer == question["correct_answer"]
    outcome = resolve_answer(
        is_correct=is_correct,
        difficulty=question["difficulty"],
        current_streak=game.current_streak,
        torches_remaining=game.torches_remaining,
    )

    previous_streak = game.current_streak
    game.current_streak = outcome.new_streak
    game.longest_streak = max(
        game.longest_streak,
        previous_streak + 1 if is_correct else game.longest_streak,
    )
    game.score += outcome.points_awarded

    if is_correct:
        game.correct_answers += 1
        game.rooms_completed += 1
        game.current_room += 1
    else:
        game.incorrect_answers += 1
        game.torches_remaining = max(0, game.torches_remaining - 1)

    attempt = QuestionAttempt(
        session_id=game.id,
        question_id=question["id"],
        question_text=question["question"],
        selected_answer=selected_answer,
        correct_answer=question["correct_answer"],
        explanation=question["explanation"],
        topic=question["topic"],
        correct=is_correct,
    )
    db.add(attempt)

    treasure = None
    if outcome.treasure_unlocked:
        treasure_data = random.choice(TREASURES)
        treasure = SessionTreasure(
            session_id=game.id,
            name=treasure_data["name"],
            description=treasure_data["description"],
        )
        db.add(treasure)
        game.treasures_found += 1

    if game.torches_remaining <= 0:
        game.game_over = True
        game.completed_at = datetime.utcnow()

    if game.current_room > game.total_rooms:
        game.completed = True
        game.completed_at = datetime.utcnow()

    db.commit()
    db.refresh(game)

    if outcome.treasure_unlocked and treasure:
        return templates.TemplateResponse(
            request=request,
            name="treasure.html",
            context={
                "game": game,
                "treasure": treasure,
                "fact": random.choice(TREASURE_FACTS),
                "question": question,
                "outcome": outcome,
            },
        )

    return templates.TemplateResponse(
        request=request,
        name="feedback.html",
        context={
            "game": game,
            "question": question,
            "selected_answer": selected_answer,
            "outcome": outcome,
            "max_torches": MAX_TORCHES,
        },
    )


@app.get("/game/{game_id}/continue")
def continue_game(
    game_id: int,
    db: Session = Depends(get_db),
):
    game = get_game(db, game_id)
    if game.game_over or game.completed:
        return RedirectResponse(url=f"/game/{game.id}/results", status_code=303)
    return RedirectResponse(url=f"/game/{game.id}", status_code=303)


@app.get("/game/{game_id}/results", response_class=HTMLResponse)
def results(
    request: Request,
    game_id: int,
    db: Session = Depends(get_db),
):
    game = get_game(db, game_id)
    mastery = mastery_from_attempts(game.attempts)
    weak_topics = [topic for topic, percent in mastery.items() if percent < 70]

    return templates.TemplateResponse(
        request=request,
        name="results.html",
        context={
            "game": game,
            "student": game.student,
            "accuracy": accuracy(game.correct_answers, game.incorrect_answers),
            "mastery": sorted(mastery.items()),
            "weak_topics": weak_topics,
        },
    )


@app.get("/game/{game_id}/review", response_class=HTMLResponse)
def review_mistakes(
    request: Request,
    game_id: int,
    db: Session = Depends(get_db),
):
    game = get_game(db, game_id)
    mistakes = [attempt for attempt in game.attempts if not attempt.correct]
    return templates.TemplateResponse(
        request=request,
        name="review.html",
        context={"game": game, "mistakes": mistakes},
    )


@app.get("/health")
def health():
    return {"status": "ok"}
