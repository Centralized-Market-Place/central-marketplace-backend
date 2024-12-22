from injector import Injector

from centeral_marketplace.infrastructure.app import AppModule
from centeral_marketplace.infrastructure.json import JsonModule


def create_injector():
    return Injector(modules=create_modules())


def create_modules():
    modules = [
        AppModule(),
        JsonModule(),
    ]
    return modules