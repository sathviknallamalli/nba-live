from judgeval import JudgmentClient
from judgeval.data import Example
from judgeval.scorers import FaithfulnessScorer
from judgeval.scorers import HallucinationScorer

client = JudgmentClient()
example = Example(
    input="What's your return policy for a pair of socks?",
    actual_output="We offer a 30-day return policy for all items, including socks!",
    context=["**RETURN POLICY** all products returnable with no cost for 30-days after purchase (receipt required)."]
)
example1 = Example(
    input="What's your return policy for a pair of socks?",
    actual_output="there is no return policy",
    context=["**RETURN POLICY** all products returnable with no cost for 30-days after purchase (receipt required)."]
)

example2 = Example(
    input="What's your return policy for a pair of socks?",
    actual_output="you can only return within a week of purchase",
    context=["**RETURN POLICY** all products returnable with no cost for 30-days after purchase (receipt required)."]
)

example3 = Example(
    input="What's your return policy for a pair of socks?",
    actual_output="maybe you can return?",
    context=["**RETURN POLICY** all products returnable with no cost for 30-days after purchase (receipt required)."]
)

example4 = Example(
    input="What's your return policy for a pair of socks?",
    actual_output="there is no return policy",
    context=["**RETURN POLICY** all products returnable with no cost for 30-days after purchase (receipt required).", "a is for apple", "b is for ball", "c is for cat"]
)

example5 = Example(
    input="What's your return policy for a pair of socks?",
    actual_output="there is no return policy",
    context=["**RETURN POLICY** all products returnable with no cost for 30-days after purchase (receipt required).", "b is for ball", "c is for cat"]
)
example6 = Example(
    input="What's your return policy for a pair of socks?",
    actual_output="there is no return policy",
    context=["**RETURN POLICY** all products returnable with no cost for 30-days after purchase (receipt required).", "b is for ball", "c is for cat", "a for apple", "d is for dog"]
)
example7 = Example(
    input="What's your return policy for a pair of socks?",
    actual_output="there is no return policy. you can return within 30 days",
    context=["**RETURN POLICY** all products returnable with no cost for 30-days after purchase (receipt required).", "b is for ball", "c is for cat", "a for apple", "d is for dog", "e for everyone"]
)

# supply your own threshold
scorer = HallucinationScorer(threshold=0.6)

results = client.run_evaluation(
    eval_run_name="sathvik88",
    examples=[example, example1, example2, example3, example4, example5, example6, example7],
    scorers=[scorer],
    model="gpt-4o",
)