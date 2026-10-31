#!/usr/bin/env python3
import argparse
import json
import sys

SHAPES = {
    'hourglass': 'песочные часы',
    'pear': 'груша',
    'apple': 'яблоко',
    'rectangle': 'прямоугольник',
    'inverted': 'перевёрнутый треугольник',
    'unsure': 'не указано',
}

ALIASES = {
    'песочные часы': 'hourglass',
    'hourglass': 'hourglass',
    'груша': 'pear',
    'pear': 'pear',
    'треугольник': 'pear',
    'triangle': 'pear',
    'яблоко': 'apple',
    'apple': 'apple',
    'прямоугольник': 'rectangle',
    'rectangle': 'rectangle',
    'перевёрнутый треугольник': 'inverted',
    'перевернутый треугольник': 'inverted',
    'inverted': 'inverted',
    'inverted triangle': 'inverted',
    'не знаю': 'unsure',
    'не указано': 'unsure',
    'unsure': 'unsure',
}

RULES = {
    'hourglass': [
        'Поддержи линию талии, если пользователь хочет акцент: заправленный верх, ремень, верх с запахом, брюки с высокой посадкой.',
        'Для свободного силуэта достаточно одной мягкой вертикали: прямой жакет, длинный кардиган, пальто без жёсткого пояса.',
        'Выбирай V-, круглый или округлый вырез; открытый воротник добавляет вертикаль.',
    ],
    'pear': [
        'Поддержи баланс верха и низа: мягкая линия плеч, вырез лодочкой, V- или квадратный вырез, рубашка с воротником.',
        'Низ: прямые или широкие брюки, A-силуэт миди, клёш; ткань должна позволять сидеть и ходить.',
        'Верх заканчивай на высокой линии бедра или ниже; если низ облегает, верх и слой оставь свободнее.',
    ],
    'apple': [
        'Создавай длинную вертикаль: расстёгнутая рубашка, V- или округлый вырез, длинный кардиган, прямой жакет.',
        'Низ: прямые или широкие брюки с мягким поясом и высокой посадкой; не выбирай жёсткий пояс, если он давит.',
        'Верх из мягкой ткани, который скользит по телу, а не облегает; длина ниже линии живота часто удобнее.',
    ],
    'rectangle': [
        'Если пользователь хочет акцент на талии: ремень, заправленный трикотаж, плиссированная миди, объём в брюках или юбке.',
        'Если акцент не нужен, держи чистую прямую линию: длинный жилет, рубашка-жакет, кардиган, прямой жакет.',
        'Добавляй объём только с одной стороны — сверху или снизу, — чтобы образ не стал тяжёлым.',
    ],
    'inverted': [
        'Смягчай линию плеч: реглан, V- или округлый вырез, мягкий плечевой шов, вертикальные детали.',
        'Низ: широкие брюки, плиссировка, A-силуэт, более светлый цвет или больше объёма, чем у верха.',
        'Верхний слой: однобортный прямой или слегка расклёшенный; избегай жёстких широких плеч и эполет, если нужен баланс.',
    ],
    'unsure': [
        'Не применяй правила силуэта; опирайся на посадку, комфорт, погоду и повод.',
    ],
}


def number(value, label):
    try:
        result = float(value)
    except (TypeError, ValueError):
        raise ValueError(f'{label}: нужно число в сантиметрах') from None
    if not 30 <= result <= 250:
        raise ValueError(f'{label}: проверь мерку, ожидаю 30–250 см')
    return result


def classify(shoulders, bust, waist, hips):
    hip_over_shoulder = hips - shoulders
    hip_over_bust = hips - bust
    shoulder_over_hip = shoulders - hips
    waist_gap = min(shoulders, bust, hips) - waist
    shoulder_hip_gap = abs(shoulders - hips)
    near = []

    if hip_over_shoulder >= 5 and hip_over_bust >= 5:
        shape = 'pear'
        margin = min(hip_over_shoulder, hip_over_bust)
    elif shoulder_over_hip >= 5:
        shape = 'inverted'
        margin = shoulder_over_hip
    elif shoulder_hip_gap <= 5 and waist_gap >= 10:
        shape = 'hourglass'
        margin = min(waist_gap - 10, 5 - shoulder_hip_gap)
    elif waist >= min(bust, hips) - 2 and shoulder_hip_gap <= 7:
        shape = 'apple'
        margin = min(abs(waist - bust), abs(waist - hips))
    else:
        shape = 'rectangle'
        margin = max(0, 5 - shoulder_hip_gap)

    if abs(hip_over_shoulder - 5) <= 2 or abs(hip_over_bust - 5) <= 2:
        near.append('груша / прямоугольник')
    if abs(shoulder_over_hip - 5) <= 2:
        near.append('перевёрнутый треугольник / прямоугольник')
    if abs(waist_gap - 10) <= 2 and shoulder_hip_gap <= 7:
        near.append('песочные часы / прямоугольник')
    if abs(waist - min(bust, hips)) <= 3 and shoulder_hip_gap <= 9:
        near.append('яблоко / прямоугольник')

    if margin >= 7:
        confidence = 'высокая'
    elif margin >= 2:
        confidence = 'средняя'
    else:
        confidence = 'низкая'
    return shape, confidence, near


def self_reported(value):
    key = ALIASES.get(str(value or '').strip().lower())
    if key is None:
        raise ValueError('неизвестный силуэт: ' + str(value))
    return key


def prompt_for(shape, confidence, note=''):
    label = SHAPES[shape]
    rules = RULES[shape]
    parts = [f'Силуэт: {label} ({confidence}{", " + note if note else ""}).']
    parts.append('Учитывай деликатно: ' + ' '.join(rules))
    parts.append('Не комментируй тело, не называй его проблемным и не обещай «исправить» фигуру.')
    return ' '.join(parts)


def main():
    parser = argparse.ArgumentParser(description='Optional body-shape fit rules for the stylist.')
    parser.add_argument('--shoulders', help='ширина плеч, см')
    parser.add_argument('--bust', help='обхват груди, см')
    parser.add_argument('--waist', help='обхват талии, см')
    parser.add_argument('--hips', help='обхват бёдер, см')
    parser.add_argument('--shape', help='силуэт со слов пользователя: груша, яблоко, прямоугольник, песочные часы, перевёрнутый треугольник')
    args = parser.parse_args()

    try:
        if any([args.shoulders, args.bust, args.waist, args.hips]):
            if not all([args.shoulders, args.bust, args.waist, args.hips]):
                raise ValueError('нужны все четыре мерки: плечи, грудь, талия, бёдра')
            shoulders = number(args.shoulders, 'плечи')
            bust = number(args.bust, 'грудь')
            waist = number(args.waist, 'талия')
            hips = number(args.hips, 'бёдра')
            key, confidence, near = classify(shoulders, bust, waist, hips)
            note = 'между силуэтами: ' + ', '.join(near) if near else ''
            data = {
                'shape': SHAPES[key],
                'shape_key': key,
                'confidence': confidence,
                'alternate': near,
                'measurements': {
                    'shoulders': shoulders,
                    'bust': bust,
                    'waist': waist,
                    'hips': hips,
                },
                'rules': RULES[key],
                'prompt': prompt_for(key, confidence, note),
                'disclaimer': 'Силуэт — это ориентир для одежды, а не диагноз и не оценка тела.',
            }
        elif args.shape:
            key = self_reported(args.shape)
            data = {
                'shape': SHAPES[key],
                'shape_key': key,
                'confidence': 'со слов пользователя',
                'alternate': [],
                'measurements': None,
                'rules': RULES[key],
                'prompt': prompt_for(key, 'со слов пользователя'),
                'disclaimer': 'Силуэт — это ориентир для одежды, а не диагноз и не оценка тела.',
            }
        else:
            raise ValueError('укажи четыре мерки или --shape')
    except ValueError as error:
        print(json.dumps({'error': str(error)}, ensure_ascii=False), file=sys.stderr)
        return 2

    print(json.dumps(data, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
