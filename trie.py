class TrieNode:
    def __init__(self):
        self.children = {}
        self.is_end_of_word = False
        self.word = None  # Store the original word

class Trie:
    def __init__(self):
        self.root = TrieNode()
        self.words = []  # Store all words for substring search

    def insert(self, word):
        node = self.root
        for char in word.lower():
            if char not in node.children:
                node.children[char] = TrieNode()
            node = node.children[char]
        node.is_end_of_word = True
        node.word = word  # Store the original word
        self.words.append(word)  # Add word to the list

    def search(self, prefix):
        node = self.root
        for char in prefix.lower():
            if char not in node.children:
                return []
            node = node.children[char]
        return self._find_words_from_node(node)

    def _find_words_from_node(self, node):
        words = []
        if node.is_end_of_word:
            words.append(node.word)
        for char, child_node in node.children.items():
            words.extend(self._find_words_from_node(child_node))
        return words

    def get_suggestions(self, prefix, limit=7):
        # Find words that start with the prefix
        words = self.search(prefix)
        # Find words that contain the prefix as a substring
        similar_words = [word for word in self.words if prefix.lower() in word.lower()]
        # Combine and deduplicate the results
        all_suggestions = list(dict.fromkeys(words + similar_words))
        return all_suggestions[:limit]