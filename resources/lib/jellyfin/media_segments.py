import json
from enum import Enum
from typing import Tuple, List, Optional

class SegmentType(Enum):
    UNKNOWN = "Unknown"
    COMMERCIAL = "Commercial"
    PREVIEW = "Preview"
    RECAP = "Recap"
    OUTRO = "Outro"
    INTRO = "Intro"

class MediaSegmentItem:
    def __init__(self, segment_id: str, item_id: str, segment_type: SegmentType, start_ticks: int, end_ticks: int):
        self.segment_id = segment_id
        self.item_id = item_id
        self.segment_type = segment_type
        self.start_ticks = start_ticks
        self.end_ticks = end_ticks

    def get_segment_type_display(self):
        return self.segment_type.value

    def get_start_seconds(self):
        return self._ticks_to_seconds(self.start_ticks)

    def get_end_seconds(self):
        return self._ticks_to_seconds(self.end_ticks)

    @staticmethod
    def _ticks_to_seconds(ticks: int) -> int:
        return ticks // 10000000

    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            segment_id=data["Id"],
            item_id=data["ItemId"],
            segment_type=SegmentType(data["Type"]),
            start_ticks=data["StartTicks"],
            end_ticks=data["EndTicks"]
        )

    def __str__(self):
        return f"{self.segment_type} - {self.start_ticks} - {self.end_ticks}"

    def __eq__(self, other):
        if not isinstance(other, MediaSegmentItem):
            return NotImplemented

        return (
            self.segment_id == other.segment_id
            and self.item_id == other.item_id
            and self.segment_type == other.segment_type
            and self.get_start_seconds() == other.get_start_seconds()
            and self.get_end_seconds() == other.get_end_seconds()
        )


class MediaSegmentResponse:
    def __init__(self, items: List[MediaSegmentItem]):
        self.items = items

    def get_next_item(self, current_seconds) -> Optional[MediaSegmentItem]:
        smallest_difference = None
        item_to_return = None
        for item in self.items:
            start_seconds = item.get_start_seconds()
            end_seconds = item.get_end_seconds()

            if start_seconds < current_seconds < end_seconds:
                return item

            if start_seconds > current_seconds:
                if not smallest_difference or start_seconds - current_seconds < smallest_difference:
                    smallest_difference = start_seconds - current_seconds
                    item_to_return = item

        return item_to_return

    @classmethod
    def from_json(cls, json_dict: dict):
        items = [MediaSegmentItem.from_dict(item) for item in json_dict["Items"]]
        return cls(
            items=items,
        )

    def get_items_by_type(self, segment_type: SegmentType) -> List[MediaSegmentItem]:
        return [item for item in self.items if item.segment_type == segment_type]

    def __str__(self):
        json_dict = {
            "Items": [str(item) for item in self.items]
        }
        return json.dumps(json_dict)