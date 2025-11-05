from django.contrib.auth import get_user_model


def test_user_mnemonic_roundtrip(db):
    User = get_user_model()
    user = User.objects.create_user(username="tester", password="secret1234")
    phrase = """alpha beta gamma delta epsilon zeta eta theta iota kappa lambda mu nu xi omicron pi rho sigma tau upsilon phi chi psi omega"""
    user.set_mnemonic_phrase(phrase)
    user.save()

    assert user.check_mnemonic_phrase(phrase) is True
    assert user.check_mnemonic_phrase(phrase.replace("alpha", "wrong")) is False
