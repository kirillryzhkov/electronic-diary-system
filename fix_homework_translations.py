from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent

FILES = {
    "en": BASE_DIR / "locale" / "en" / "LC_MESSAGES" / "django.po",
    "kk": BASE_DIR / "locale" / "kk" / "LC_MESSAGES" / "django.po",
}


TRANSLATIONS = {
    "en": {
        "Домашние задания": "Homework",
        "Список всех домашних заданий в системе.": "List of all homework assignments in the system.",
        "Домашние задания, которые вы добавили для своих групп.": "Homework assignments you added for your groups.",
        "Домашние задания вашей группы.": "Homework assignments for your group.",
        "Добавить домашнее задание": "Add Homework",
        "Редактировать домашнее задание": "Edit Homework",
        "Удалить домашнее задание": "Delete Homework",
        "Подтвердите удаление домашнего задания.": "Confirm deletion of the homework assignment.",
        "Вы действительно хотите удалить это домашнее задание?": "Are you sure you want to delete this homework assignment?",
        "Домашних заданий пока нет.": "There are no homework assignments yet.",
        "Тема задания": "Assignment Topic",
        "Описание задания": "Assignment Description",
        "Срок сдачи": "Deadline",
        "Дата создания": "Created At",
    },
    "kk": {
        "Домашние задания": "Үй тапсырмалары",
        "Список всех домашних заданий в системе.": "Жүйедегі барлық үй тапсырмаларының тізімі.",
        "Домашние задания, которые вы добавили для своих групп.": "Сіз өз топтарыңызға қосқан үй тапсырмалары.",
        "Домашние задания вашей группы.": "Сіздің тобыңыздың үй тапсырмалары.",
        "Добавить домашнее задание": "Үй тапсырмасын қосу",
        "Редактировать домашнее задание": "Үй тапсырмасын өңдеу",
        "Удалить домашнее задание": "Үй тапсырмасын жою",
        "Подтвердите удаление домашнего задания.": "Үй тапсырмасын жоюды растаңыз.",
        "Вы действительно хотите удалить это домашнее задание?": "Бұл үй тапсырмасын шынымен жойғыңыз келе ме?",
        "Домашних заданий пока нет.": "Әзірге үй тапсырмалары жоқ.",
        "Тема задания": "Тапсырма тақырыбы",
        "Описание задания": "Тапсырма сипаттамасы",
        "Срок сдачи": "Тапсыру мерзімі",
        "Дата создания": "Жасалған күні",
    },
}


def po_escape(text: str) -> str:
    return text.replace("\\", "\\\\").replace('"', '\\"')


def po_unescape(text: str) -> str:
    return text.replace('\\"', '"').replace("\\\\", "\\")


def extract_po_string(lines, start_index):
    line = lines[start_index]
    value = line.split(" ", 1)[1].strip()

    parts = []

    if value.startswith('"') and value.endswith('"'):
        parts.append(value[1:-1])

    i = start_index + 1

    while i < len(lines):
        current = lines[i].strip()

        if current.startswith('"') and current.endswith('"'):
            parts.append(current[1:-1])
            i += 1
        else:
            break

    return po_unescape("".join(parts)), i


def get_entry_msgid(entry: str) -> str | None:
    lines = entry.splitlines()

    for index, line in enumerate(lines):
        if line.startswith("msgid "):
            msgid, _ = extract_po_string(lines, index)
            return msgid

    return None


def replace_entry_msgstr(entry: str, translation: str) -> str:
    lines = entry.splitlines()
    new_lines = []

    i = 0
    while i < len(lines):
        line = lines[i]

        if line.startswith("#, fuzzy"):
            i += 1
            continue

        if line.startswith("#|"):
            i += 1
            continue

        if line.startswith("msgstr "):
            new_lines.append(f'msgstr "{po_escape(translation)}"')
            i += 1

            while i < len(lines) and lines[i].strip().startswith('"'):
                i += 1

            continue

        new_lines.append(line)
        i += 1

    return "\n".join(new_lines)


def update_po_file(file_path: Path, translations: dict[str, str]) -> None:
    if not file_path.exists():
        print(f"Файл не найден: {file_path}")
        return

    content = file_path.read_text(encoding="utf-8")
    entries = content.split("\n\n")

    found = set()
    updated_entries = []

    for entry in entries:
        msgid = get_entry_msgid(entry)

        if msgid in translations:
            entry = replace_entry_msgstr(entry, translations[msgid])
            found.add(msgid)

        updated_entries.append(entry)

    missing = set(translations.keys()) - found

    for msgid in sorted(missing):
        updated_entries.append(
            f'msgid "{po_escape(msgid)}"\n'
            f'msgstr "{po_escape(translations[msgid])}"'
        )

    new_content = "\n\n".join(updated_entries).strip() + "\n"
    file_path.write_text(new_content, encoding="utf-8")

    print(f"Обновлён файл: {file_path}")
    print(f"Заменено переводов: {len(found)}")
    print(f"Добавлено новых переводов: {len(missing)}")


def main():
    for lang, file_path in FILES.items():
        print(f"\nОбработка языка: {lang}")
        update_po_file(file_path, TRANSLATIONS[lang])


if __name__ == "__main__":
    main()